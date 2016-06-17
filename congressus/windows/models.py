from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User

from autoslug import AutoSlugField

from events.models import Event
from tickets.models import MultiPurchase

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db.models import Sum


PAYMENT_TYPES = (
    ('cash', _('Cash')),
    ('card', _('Credit Card')),
)


CASH_MOVEMENT_TYPES = (
    ('add', _('Add')),
    ('remove', _('Remove')),
)


class TicketWindow(models.Model):
    event = models.ForeignKey(Event, related_name='windows')

    name = models.CharField(_('name'), max_length=200)
    slug = AutoSlugField(populate_from='name')
    cash = models.IntegerField(_('cash in the ticket window'), default=0)

    location = models.CharField(max_length=500, blank=True, null=True)

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
        sales = sales.aggregate(sold=Sum('price'))
        return sales['sold'] or 0

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

    def __str__(self):
        return self.name


class TicketWindowSale(models.Model):
    window = models.ForeignKey(TicketWindow, related_name='sales')
    user = models.ForeignKey(User, related_name='sales')
    purchase = models.ForeignKey(MultiPurchase, related_name='sales')

    price = models.PositiveIntegerField(default=0)
    payed = models.PositiveIntegerField(default=0)
    change = models.PositiveIntegerField(default=0)
    payment = models.CharField(max_length=10, choices=PAYMENT_TYPES, default='cash')

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s - %s' % (self.user, self.window, self.purchase)

    def tickets(self):
        return self.purchase.tickets.all()


class TicketWindowCashMovement(models.Model):
    window = models.ForeignKey(TicketWindow, related_name='movements')
    type = models.CharField(max_length=10, choices=CASH_MOVEMENT_TYPES, default='add')
    amount = models.PositiveIntegerField(default=0)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s - %s - %s" % (self.window, self.type, self.amount)


def update_window_cash(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        amount = 0
        if isinstance(instance, TicketWindowSale):
            if instance.payment == 'cash':
                amount = instance.price
        elif isinstance(instance, TicketWindowCashMovement):
            if instance.type == 'add':
                amount = instance.amount
            else:
                amount = -instance.amount
        instance.window.cash += int(amount)
        instance.window.save()

post_save.connect(update_window_cash, TicketWindowCashMovement)
post_save.connect(update_window_cash, TicketWindowSale)
