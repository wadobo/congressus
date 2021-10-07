import websocket
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.conf import settings

from autoslug import AutoSlugField

from events.models import Event, TicketTemplate
from tickets.models import MultiPurchase

from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.db.models.signals import pre_save

from django.db.models import Sum


PAYMENT_TYPES = (
    ('cash', _('Cash')),
    ('card', _('Credit Card')),
)


CASH_MOVEMENT_TYPES = (
    ('change', _('Change')),
    ('preturn', _('Parcial return')),
    ('return', _('Final return')),
)


SINGLEROW_POS = (
    ('R', _('Right')),
    ('L', _('Left')),
)


class TicketWindow(models.Model):
    event = models.ForeignKey(Event, related_name='windows', verbose_name=_('event'), on_delete=models.CASCADE)

    name = models.CharField(_('name'), max_length=200)
    number = models.IntegerField(_('number'), default=1, blank=True, null=True)
    slug = AutoSlugField(populate_from='name')
    code = models.CharField(_('code'), max_length=5, help_text=_('code to show in tickets'))
    cash = models.FloatField(_('cash in the ticket window'), default=0)
    user = models.ForeignKey(User, verbose_name=_('user'), blank=True, null=True, on_delete=models.CASCADE)

    location = models.CharField(_('location'), max_length=500, blank=True, null=True)
    online = models.BooleanField(_('online'), default=False)
    singlerow = models.BooleanField(_('single row'), default=False)
    singlerow_pos = models.CharField(_('single row position'), default="R", choices=SINGLEROW_POS, max_length=1)

    supplement = models.FloatField(_('increments or decrements the ticket price for this window'), default=0)

    print_close_timeout = models.FloatField(
        _('PDF ticket window close timeout'),
        help_text=_('Time to auto close the ticket PDF popup window, use 0 to disable auto close'),
        default=1.0
    )
    shortcuts = JSONField(default=dict({'add': 145, 'sub': 19, 'onoff': 42}))
    autocall_singlerow = models.BooleanField(_('autocall singlerow'), default=True)
    number_of_calls = models.PositiveSmallIntegerField(_('number of call'),
            help_text=_('Number of calls created to singlerow when open ticket windows'),
            default=1)
    templates = models.ManyToManyField(TicketTemplate)

    class Meta:
        verbose_name = _('ticket window')
        verbose_name_plural = _('ticket windows')
        ordering = ['-event', 'name']

    def get_sales(self, date, **kwargs):
        if not date:
            date = timezone.now()

        sales = TicketWindowSale.objects.filter(
            window=self,
            date__year=date.year,
            date__month=date.month, date__day=date.day, **kwargs)

        return sales

    def tickets_today(self, date=None):
        sales = self.get_sales(date)
        sales = sum(i.purchase.tickets.count() for i in sales)
        return sales

    def sold_today(self, date=None):
        sales = self.get_sales(date)
        sales = sales.aggregate(sold=Sum('price'))
        return sales['sold'] or 0

    def sold_today_cash(self, date=None):
        sales = self.get_sales(date, payment='cash')
        sales = sales.aggregate(sold=Sum('price'))
        return sales['sold'] or 0

    def sold_today_card(self, date=None):
        sales = self.get_sales(date, payment='card')
        sales = sales.aggregate(sold=Sum('price'))
        return sales['sold'] or 0

    def get_price(self, session):
        return session.window_price + self.supplement

    def get_available_templates(self) -> dict[int, str]:
        return {tpl.id: tpl.name for tpl in self.templates.all()}

    def __str__(self):
        return "{0} - {1}".format(self.event.name, self.name)


class TicketWindowSale(models.Model):
    window = models.ForeignKey(TicketWindow, related_name='sales', verbose_name=_('window'), on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='sales', verbose_name=_('user'), blank=True, null=True, on_delete=models.CASCADE)
    purchase = models.ForeignKey(MultiPurchase, related_name='sales', verbose_name=_('multipurchase'), on_delete=models.CASCADE)

    price = models.FloatField(_('price'), default=0)
    payed = models.FloatField(_('payed'), default=0)
    change = models.FloatField(_('change'), default=0)
    payment = models.CharField(_('payment'), max_length=10, choices=PAYMENT_TYPES, default='cash')

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('ticket window sale')
        verbose_name_plural = _('ticket window sales')

    def __str__(self):
        return '%s - %s - %s' % (self.user, self.window, self.purchase)

    def tickets(self):
        return self.purchase.tickets.all()


class TicketWindowCashMovement(models.Model):
    window = models.ForeignKey(TicketWindow, related_name='movements', verbose_name=_('window'), on_delete=models.CASCADE)
    type = models.CharField(_('type'), max_length=10, choices=CASH_MOVEMENT_TYPES, default='change')
    amount = models.FloatField(_('amount'), default=0)

    note = models.TextField(_('Note'), blank=True, null=True)

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('ticket window cash movement')
        verbose_name_plural = _('ticket window cash movements')
        ordering = ['id']

    def signed_amount(self):
        if self.type == 'change':
            amount = self.amount
        else:
            amount = -self.amount
        return amount

    def __str__(self):
        return "%s - %s - %s" % (self.window, self.type, self.amount)


def send_cash_change_ws(slug, wtype, amount):
    # Only affect to dashboard
    try:
        ws = websocket.WebSocket()
        ws.connect('ws://' + settings.WS_SERVER)
        now = datetime.now().isoformat()
        args = 'add_change {0} {1} {2} {3} {4}'.format(slug, now, wtype, 'cash', amount)
        ws.send(args)
        ws.close()
    except:
        pass


def update_window_cash_sale(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        amount = 0
        if instance.payment == 'cash':
            amount = instance.price
        instance.window.cash += amount
        instance.window.save()


def update_window_cash_movement(sender, instance, **kwargs):
    prev = TicketWindowCashMovement.objects.filter(id=instance.id).first()
    if prev: # modify: remove previous change
        if prev.type == 'change':
            amount = prev.amount
        else:
            amount = -prev.amount
        instance.window.cash -= amount
        send_cash_change_ws(prev.window.slug, prev.type, -amount)
    # new or modify: apply change
    amount = instance.signed_amount()
    send_cash_change_ws(instance.window.slug, instance.type, amount)

    instance.window.cash += amount
    instance.window.save()


def delete_window_cash_movement(sender, instance, **kwargs):
    amount = instance.signed_amount()
    send_cash_change_ws(instance.window.slug, instance.type, -amount)
    instance.window.cash -= amount
    instance.window.save()

post_save.connect(update_window_cash_sale, TicketWindowSale)
pre_save.connect(update_window_cash_movement, TicketWindowCashMovement)
post_delete.connect(delete_window_cash_movement, TicketWindowCashMovement)
