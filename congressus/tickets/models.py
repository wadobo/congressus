import string
import random
import json
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.template import Context
from django.template import Template
from django.template.loader import get_template

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.urlresolvers import reverse

from events.models import Event, InvCode
from events.models import Session
from events.models import Discount
from events.models import SeatLayout
from tickets.utils import generate_pdf
from tickets.utils import generate_thermal
from tickets.utils import concat_pdf


WARNING_TYPES = (
    ('req', _('Required')),
)

SEATHOLD_TYPES = (
    ('H', _('Holded')),
    ('C', _('Confirming')),
    ('P', _('Paying')),
    ('R', _('Reserved')),
)

PAYMENT_TYPES = (
    ('tpv', _('TPV')),
    ('paypal', _('Paypal')),
    ('stripe', _('Stripe')),
    ('twcash', _('Cash, Ticket Window')),
    ('twtpv', _('TPV, Ticket Window')),
)


class BaseTicketMixing:
    '''
    Common base class for ticket and MultiPurchase to avoid django model
    inheritance, but to use the same code for methods
    '''

    def space(self):
        return self.session.space

    def event(self):
        return self.space().event

    def is_order_used(self, order):
        tk = Ticket.objects.filter(order=order).exists()
        mp = MultiPurchase.objects.filter(order=order).exists()
        return mp or tk

    def gen_order(self, save=True):
        chars = string.ascii_uppercase + string.digits
        l = 8
        if hasattr(settings, 'ORDER_SIZE'):
            l = settings.ORDER_SIZE

        order = ''
        used = True
        reserved = True
        while used or reserved:
            order = ''.join(random.choice(chars) for _ in range(l))
            used = self.is_order_used(order)
            reserved = order.startswith(settings.INVITATION_ORDER_START)

        self.order = order
        if save:
            self.save()

    def gen_order_tpv(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.order_tpv = timezone.now().strftime('%y%m%d')
        self.order_tpv += ''.join(random.choice(chars) for _ in range(6))
        self.save()

    def get_price(self):
        total = self.session.price
        if self.mp and self.mp.discount and self.mp.discount.unit:
            total = self.mp.discount.apply_to(total)
        return total

    def get_tax(self):
        return self.session.tax

    def get_window_price(self):
        total = self.session.window_price
        if self.mp and self.mp.discount and self.mp.discount.unit:
            total = self.mp.discount.apply_to(total)
        return total

    def send_reg_email(self):
        tmpl = get_template('emails/reg.txt')
        body = tmpl.render({'ticket': self})
        email = EmailMessage(_('New Register / %s') % self.event(),
                             body, settings.FROM_EMAIL,
                             [self.event().admin], reply_to=[self.email])
        email.send(fail_silently=False)

    def send_confirm_email(self):
        self.confirm_sent = True
        self.save()

        if self.email == settings.FROM_EMAIL:
            # ticket from ticket window
            return

        # email to admin
        tmpl = get_template('emails/confirm.txt')
        body = tmpl.render({'ticket': self})
        email = EmailMessage(_('Confirmed / %s') % self.event(),
                             body, settings.FROM_EMAIL,
                             [self.event().admin], reply_to=[self.email])
        email.send(fail_silently=False)

        # email to user
        e = self.event().get_email()

        extra = json.loads(self.extra_data)
        if e:
            subject = Template(e.subject).render(Context({'ticket': self, 'extra': extra}))
            body = Template(e.body).render(Context({'ticket': self, 'extra': extra}))
        else:
            tmpl = get_template('emails/subject-confirm-user.txt')
            subject = tmpl.render({'ticket': self, 'extra': extra})
            tmpl = get_template('emails/confirm-user.txt')
            body = tmpl.render({'ticket': self, 'extra': extra})

        body = body.replace('TICKETID', self.order)

        email = EmailMessage(subject.strip(), body, settings.FROM_EMAIL, [self.email])

        if e:
            # adding attachments
            for att in e.attachs.all():
                email.attach_file(att.attach.path)

        filename = 'ticket_%s.pdf' % self.order
        email.attach(filename, self.gen_pdf(), 'application/pdf')
        email.send(fail_silently=False)

    def get_absolute_url(self):
        url = 'payment' if not self.confirmed else 'thanks'

        order = self.order
        if hasattr(self, 'mp') and self.mp:
            order = self.mp.order

        return reverse(url, kwargs={'order': order})

    def is_mp(self):
        return False

    def hold_seats(self):
        all_tk = []
        if self.is_mp():
            all_tk = self.tickets.only("session", "seat_layout", "seat").filter(session__space__numbered=True)
        elif self.session.space.numbered:
            all_tk = [self]

        # Save reserved ticket in SeatHold
        for t in all_tk:
            tsh, created = TicketSeatHold.objects.get_or_create(
                session=t.session,
                layout=t.seat_layout,
                seat=t.seat,
                type='R'
            )
            tsh.client='CONFIRMED'
            tsh.save()

    def remove_hold_seats(self):
        all_tk = []
        if self.is_mp():
            all_tk = self.tickets.filter(session__space__numbered=True)
        elif self.session.space.numbered:
            all_tk = [self]

        # Save reserved ticket in SeatHold
        for t in all_tk:
            TicketSeatHold.objects.filter(
                    session=t.session,
                    layout=t.seat_layout,
                    type='R',
                    seat=t.seat
            ).delete()

    def confirm(self, method='tpv'):
        self.confirmed = True
        self.payment_method = method

        if self.is_mp():
            self.tickets.update(payment_method=method)

        self.hold_seats()
        self.save()

    def set_error(self, error, info):
        self.tpv_error = error
        self.tpv_error_info = info
        self.save()


class BaseExtraData:
    def get_extra_data(self, key):
        data = {}
        if not self.extra_data:
            return None
        else:
            data = json.loads(self.extra_data)
        return data.get(key, None)

    def set_extra_data(self, key, value):
        data = json.loads(self.extra_data or '{}')
        data[key] = value
        self.extra_data = json.dumps(data)

    def get_extras_dict(self):
        extras = {}
        for field in self.event().fields.all():
            extras[field.label] = self.get_extra_data(field.label)
        return extras

    def get_extras(self):
        extras = []
        for field in self.event().fields.all():
            extras.append({
                'field': field,
                'value': self.get_extra_data(field.label)
            })
        return extras

    def get_extra_sessions(self):
        d = self.get_extra_data('extra_sessions')
        return d or []

    def get_extra_session(self, pk):
        for extra in self.get_extra_sessions():
            if extra['session'] == pk:
                return extra
        return None

    def set_extra_session_to_used(self, pk):
        data = self.get_extra_sessions()
        for extra in data:
            if extra.get('session') == pk:
                extra['used'] = True
                dt = timezone.localtime(timezone.now())
                extra['used_date'] = dt.strftime(settings.DATETIME_FORMAT)
                break
        self.set_extra_data('extra_sessions', data)

    def save_extra_sessions(self):
        data = []
        for extra in self.session.orig_sessions.all():
            prev = self.get_extra_session(extra.extra.id)
            data.append({
                'session': extra.extra.id,
                'start': timezone.make_naive(extra.start).strftime(settings.DATETIME_FORMAT),
                'end': timezone.make_naive(extra.end).strftime(settings.DATETIME_FORMAT),
                'used': prev['used'] if prev else extra.used
            })
        self.set_extra_data('extra_sessions', data)


class MultiPurchase(models.Model, BaseTicketMixing, BaseExtraData):
    ev = models.ForeignKey(Event, related_name='mps', verbose_name=_('event'))

    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)

    tpv_error = models.CharField(_('error TPV'), max_length=200, blank=True, null=True)
    tpv_error_info = models.CharField(_('error TPV info'), max_length=200, blank=True, null=True)

    payment_method = models.CharField(_('payment method'), max_length=10, choices=PAYMENT_TYPES, blank=True, null=True)

    created = models.DateTimeField(_('created at'), auto_now_add=True)
    confirmed_date = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(_('confirmed'), default=False)
    confirm_sent = models.BooleanField(_('confirmation sent'), default=False)
    discount = models.ForeignKey(Discount, related_name='mps', verbose_name=_('discount'),
            blank=True, null=True)

    # Form Fields
    email = models.EmailField(_('email'))

    extra_data = models.TextField(_('extra data'), blank=True, null=True)

    def save(self, *args, **kw):
        if self.pk is not None:
            orig = MultiPurchase.objects.get(pk=self.pk)
            confirm = self.confirmed != orig.confirmed
        else:
            confirm = True

        if confirm:
            for t in self.tickets.all():
                t.confirmed = self.confirmed
                t.save()
            if self.confirmed:
                self.confirmed_date = timezone.now()

        super(MultiPurchase, self).save(*args, **kw)

    def space(self):
        ''' Multiple spaces '''
        return None

    def event(self):
        return self.ev

    def get_price(self):
        total = sum(i.get_price() for i in self.tickets.all())
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def get_window_price(self):
        total = sum(i.get_window_price() for i in self.tickets.all())
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def get_real_price(self):
        if not self.tickets.count():
            return 0

        if self.tickets.first().sold_in_window:
            total = sum(i.get_window_price() for i in self.tickets.all())
        else:
            total = sum(i.get_price() for i in self.tickets.all())
        if self.discount and not self.discount.unit:
            total = self.discount.apply_to(total)
        return total

    def is_mp(self):
        return True

    def gen_pdf(self):
        files = []
        for ticket in self.all_tickets():
            files.append(generate_pdf(ticket, asbuf=True))
        return concat_pdf(files)

    def gen_thermal(self):
        files = []
        for ticket in self.all_tickets():
            files.append(generate_thermal(ticket, asbuf=True))
        return concat_pdf(files)

    def all_tickets(self):
        return self.tickets.all().order_by('session__start')

    def delete(self, *args, **kwargs):
        self.remove_hold_seats()
        super(MultiPurchase, self).delete(*args, **kwargs)

    def window_code(self):
        '''
        ONLMMDDHHMM
        '''

        prefix = 'ONL'
        postfix = timezone.localtime(self.created).strftime('%m%d%H%M')

        from windows.models import TicketWindowSale
        prefix = TicketWindowSale.objects.values_list("window__code", flat=True).get(purchase=self)

        return prefix + postfix

    class Meta:
        ordering = ['-created']
        verbose_name = _('multipurchase')
        verbose_name_plural = _('multipurchases')

    def __str__(self):
        return self.order


class Ticket(models.Model, BaseTicketMixing, BaseExtraData):
    session = models.ForeignKey(Session, related_name='tickets', verbose_name=_('event'))

    inv = models.OneToOneField(InvCode, blank=True, null=True, verbose_name=_('invitation code'))

    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)

    tpv_error = models.CharField(_('error TPV'), max_length=200, blank=True, null=True)
    tpv_error_info = models.CharField(_('error TPV info'), max_length=200, blank=True, null=True)

    payment_method = models.CharField(_('payment method'), max_length=10, choices=PAYMENT_TYPES, blank=True, null=True)

    created = models.DateTimeField(_('created at'), auto_now_add=True)
    confirmed_date = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(_('confirmed'), default=False)
    confirm_sent = models.BooleanField(_('confirmation sent'), default=False)
    sold_in_window = models.BooleanField(_('sold in window'), default=False)

    # row-col
    seat = models.CharField(_('seat'), max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True, verbose_name=_('seat layout'))

    # Form Fields
    email = models.EmailField(_('email'))
    extra_data = models.TextField(_('extra data'), blank=True, null=True)

    mp = models.ForeignKey(MultiPurchase, related_name='tickets', null=True, blank=True, verbose_name=_('multipurchase'))

    # duplicated data to optimize queries
    session_name = models.CharField(_('session name'), max_length=200, null=True, blank=True)
    space_name = models.CharField(_('space name'), max_length=200, null=True, blank=True)
    event_name = models.CharField(_('event name'), max_length=200, null=True, blank=True)
    price = models.FloatField(_('price'), null=True)
    tax = models.IntegerField(_('tax'), null=True)
    start = models.DateTimeField(_('start date'), null=True)
    end = models.DateTimeField(_('end date'), null=True)
    seat_layout_name = models.CharField(_('seat layout name'), max_length=200, null=True, blank=True)
    gate_name = models.CharField(_('gate name'), max_length=100, null=True, blank=True)

    # field to control the access
    used = models.BooleanField(_('used'), default=False)
    used_date = models.DateTimeField(_('ticket used date'), blank=True, null=True)

    class Meta:
        ordering = ['-created']
        verbose_name = _('ticket')
        verbose_name_plural = _('tickets')

    def __str__(self):
        return self.order

    def get_gate_name(self):
        return self.gate_name

    def save(self, *args, **kw):
        if self.pk is not None:
            orig = Ticket.objects.get(pk=self.pk)
            confirm = self.confirmed != orig.confirmed
            if orig.used != self.used:
                if self.used:
                    self.used_date = timezone.now()
                else:
                    self.used_date = None
        else:
            confirm = True

        if confirm and self.confirmed:
            self.confirmed_date = timezone.now()

        super(Ticket, self).save(*args, **kw)

    def delete(self, *args, **kwargs):
        self.remove_hold_seats()
        super(Ticket, self).delete(*args, **kwargs)

    def cseat(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return _('L%(layout)s-R%(row)s-C%(col)s') % {'layout': self.seat_layout.name, 'row': row, 'col': column}
    cseat.short_description = _('seat')

    def seat_row(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return row

    def seat_column(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return column

    def update_mp_extra_data(self):
        if not self.mp or not self.mp.extra_data:
            return

        data = json.loads(self.mp.extra_data)
        for k, v in data.items():
            self.set_extra_data(k, v)

    def fill_duplicated_data(self):
        self.session_name = self.session.name
        self.space_name = self.space().name
        self.event_name = self.event().name
        self.price = self.session.price
        self.tax = self.session.tax
        self.start = self.session.start
        self.end = self.session.end
        if self.seat_layout:
            self.seat_layout_name = self.seat_layout.name
            if self.seat_layout.gate:
                self.gate_name = self.seat_layout.gate.name

        self.update_mp_extra_data()
        self.save_extra_sessions()

    def gen_pdf(self):
        return generate_pdf(self)

    def gen_thermal(self):
        return generate_thermal(self)

    def window_code(self):
        '''
        ONLMMDDHHMM
        '''

        prefix = 'ONL'
        postfix = timezone.localtime(self.created).strftime('%m%d%H%M')
        if self.sold_in_window:
            from windows.models import TicketWindowSale
            prefix = TicketWindowSale.objects.values_list("window__code", flat=True).get(purchase__tickets=self)

        return prefix + postfix

    def get_real_price(self):
        if self.sold_in_window:
            return self.get_window_price()
        else:
            return self.get_price()


class TicketWarning(models.Model):
    name = models.CharField(max_length=50)

    ev = models.ForeignKey(Event, related_name='warnings', verbose_name=_('event'))
    sessions1 = models.ManyToManyField(Session, related_name='warnings1', verbose_name=_('sessions1'))
    sessions2 = models.ManyToManyField(Session, related_name='warnings2', verbose_name=_('sessions2'))
    message = models.TextField(_('message'))
    type = models.CharField(_('type'), max_length=10, choices=WARNING_TYPES, default="req")

    class Meta:
        verbose_name = _('ticket warning')
        verbose_name_plural = _('ticket warnings')

    def sessions1_ids(self):
        return ','.join(str(s.id) for s in self.sessions1.all())

    def sessions2_ids(self):
        return ','.join(str(s.id) for s in self.sessions2.all())

    def __str__(self):
        return self.name


class TicketSeatHold(models.Model):
    client = models.CharField(_('client'), max_length=20)
    session = models.ForeignKey(Session, related_name='seat_holds', verbose_name=_('session'))
    layout = models.ForeignKey(SeatLayout, verbose_name=_('layout'))
    seat = models.CharField(_('seat'), max_length=20, help_text="row-col")
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(_('type'), max_length=2, choices=SEATHOLD_TYPES, default="H")

    class Meta:
        verbose_name = _('ticket seat hold')
        verbose_name_plural = _('ticket seat holds')

    def __str__(self):
        return self.seat


def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


def ticket_seat_hold_confirmed(sender, instance, **kwargs):
        tsh_list = TicketSeatHold.objects.filter(session=instance.session, 
                                                 layout=instance.layout, 
                                                 seat=instance.seat).exclude(pk=instance.pk).delete()


post_save.connect(ticket_seat_hold_confirmed, TicketSeatHold)
post_save.connect(confirm_email, Ticket)
post_save.connect(confirm_email, MultiPurchase)
