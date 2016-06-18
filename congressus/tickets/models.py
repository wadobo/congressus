import string
import random
import json
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import get_template

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.urlresolvers import reverse

from events.models import Event, InvCode
from events.models import Session
from events.models import SeatLayout
from tickets.utils import generate_pdf
from tickets.utils import concat_pdf


WARNING_TYPES = (
    ('req', _('Required')),
)


class BaseTicketMixing:
    '''
    Common base class for ticket and MultiPurchase to avoid django model
    inheritance, but to use the same code for methods
    '''

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

    def get_extras(self):
        extras = []
        for field in self.event().fields.all():
            extras.append({
                'field': field,
                'value': self.get_extra_data(field.label)
            })
        return extras

    def space(self):
        return self.session.space

    def event(self):
        return self.space().event

    def is_order_used(self, order):
        tk = Ticket.objects.filter(order=order).exists()
        mp = MultiPurchase.objects.filter(order=order).exists()
        return mp or tk

    def gen_order(self):
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
            reserved = order.startswith('00001') or order.startswith('00002')

        self.order = order
        self.save()

    def gen_order_tpv(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.order_tpv = timezone.now().strftime('%y%m%d')
        self.order_tpv += ''.join(random.choice(chars) for _ in range(6))
        self.save()

    def get_price(self):
        # TODO manage ticket type
        return self.session.price

    def get_window_price(self):
        return self.session.window_price

    def send_reg_email(self):
        tmpl = get_template('emails/reg.txt')
        body = tmpl.render({'ticket': self})
        email = EmailMessage(_('New Register / %s') % self.event(),
                             body, settings.FROM_EMAIL, [self.event().admin])
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
                             body, settings.FROM_EMAIL, [self.event().admin])
        email.send(fail_silently=False)

        # email to user
        e = self.event().get_email()
        if e:
            subject = e.subject
            body = e.body
        else:
            tmpl = get_template('emails/confirm-user.txt')
            subject = _('Ticket Confirmed / %s') % self.event()
            body = tmpl.render({'ticket': self})

        body = body.replace('TICKETID', self.order)

        email = EmailMessage(subject, body, settings.FROM_EMAIL, [self.email])

        if e:
            # adding attachments
            for att in e.attachs.all():
                email.attach_file(att.attach.path)

        email.attach(filename, ticket.gen_pdf(), 'application/pdf')
        email.send(fail_silently=False)

    def get_absolute_url(self):
        return reverse('payment', kwargs={'order': self.order})

    def confirm(self):
        self.confirmed = True
        self.confirmed_date = timezone.now()
        self.save()


class MultiPurchase(models.Model, BaseTicketMixing):
    ev = models.ForeignKey(Event, related_name='mps')

    order = models.CharField(_('Order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('Order TPV'), max_length=12, blank=True, null=True)

    created = models.DateTimeField(_('Created at'), auto_now_add=True)
    confirmed_date = models.DateTimeField(_('Confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    confirm_sent = models.BooleanField(default=False)

    # Form Fields
    email = models.EmailField(_('Email'))

    extra_data = models.TextField(blank=True, null=True)

    def space(self):
        ''' Multiple spaces '''
        return None

    def event(self):
        return self.ev

    def get_price(self):
        return sum(i.get_price() for i in self.tickets.all())

    def get_window_price(self):
        return sum(i.get_window_price() for i in self.tickets.all())

    def confirm(self):
        self.confirmed = True
        self.confirmed_date = timezone.now()
        for t in self.tickets.all():
            t.confirmed = True
            t.confirmed_date = timezone.now()
            t.save()
        self.save()

    def is_mp(self):
        return True

    def gen_pdf(self):
        files = []
        for ticket in self.all_tickets():
            files.append(generate_pdf(ticket, asbuf=True))
        return concat_pdf(files)

    def all_tickets(self):
        return self.tickets.all().order_by('session__start')

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order


class Ticket(models.Model, BaseTicketMixing):
    session = models.ForeignKey(Session, related_name='tickets')

    inv = models.OneToOneField(InvCode, blank=True, null=True)

    order = models.CharField(_('Order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('Order TPV'), max_length=12, blank=True, null=True)

    created = models.DateTimeField(_('Created at'), auto_now_add=True)
    confirmed_date = models.DateTimeField(_('Confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    confirm_sent = models.BooleanField(default=False)
    sold_in_window = models.BooleanField(default=False)

    seat = models.CharField(max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True)

    # Form Fields
    email = models.EmailField(_('Email'))
    extra_data = models.TextField(blank=True, null=True)

    mp = models.ForeignKey(MultiPurchase, related_name='tickets', null=True, blank=True)

    # duplicated data to optimize queries
    session_name = models.CharField(max_length=200, null=True, blank=True)
    space_name = models.CharField(max_length=200, null=True, blank=True)
    event_name = models.CharField(max_length=200, null=True, blank=True)
    price = models.IntegerField(null=True)
    tax = models.IntegerField(null=True)
    start = models.DateTimeField(_('start date'), null=True)
    end = models.DateTimeField(_('end date'), null=True)
    seat_layout_name = models.CharField(max_length=200, null=True, blank=True)
    gate_name = models.CharField(max_length=100, null=True, blank=True)

    # field to control the access
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order

    def cseat(self):
        if not self.seat:
            return None
        row, column = self.seat.split('-')
        return _('L%(layout)s-R%(row)s-C%(col)s') % {'layout': self.seat_layout.name, 'row': row, 'col': column}

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

    def gen_pdf(self):
        return generate_pdf(self)


class TicketWarning(models.Model):
    name = models.CharField(max_length=50)

    ev = models.ForeignKey(Event, related_name='warnings')
    sessions1 = models.ManyToManyField(Session, related_name='warnings1')
    sessions2 = models.ManyToManyField(Session, related_name='warnings2')
    message = models.TextField()
    type = models.CharField(max_length=10, choices=WARNING_TYPES, default="req")

    def sessions1_ids(self):
        return ','.join(str(s.id) for s in self.sessions1.all())

    def sessions2_ids(self):
        return ','.join(str(s.id) for s in self.sessions2.all())

    def __str__(self):
        return self.name


class TicketSeatHold(models.Model):
    client = models.CharField(max_length=20)
    session = models.ForeignKey(Session, related_name='seat_holds')
    layout = models.ForeignKey(SeatLayout)
    seat = models.CharField(max_length=20, help_text="row-col")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.seat


class BasePassInvitation:
    ''' Common base class for Passes and Invitations. '''

    def gen_order(self, starts):
        """ Generate order for passes and invitations """
        if isinstance(self, Pass):
            starts = '00001'
        elif isinstance(self, Invitation):
            starts = '00002'
        else:
            assert('Invalid Model')
        chars = string.ascii_uppercase + string.digits
        l = 8
        if hasattr(settings, 'ORDER_SIZE'):
            l = settings.ORDER_SIZE
            l -= len(starts)

        order = ''
        used = True
        reserved = True
        while used:
            order = ''.join(random.choice(chars) for _ in range(l))
            order = starts + order
            used = self.is_order_used(order)
        self.order = order
        self.save()

    def is_order_used(self, order):
        if order.startswith('00001'):
            p = Pass.objects.filter(order=order).exists()
        elif order.startswith('00002'):
            i = Invitation.objects.filter(order=order).exists()
        else:
            assert('Invalid order')
        return p or i



PASSES_TYPES = (
    ('org', _('Organization Pass')),
    ('vip', _('Vip Pass')),
    ('par', _('Rancher Partner Pass')),
    ('sym', _('Sympathizer Pass')),
    ('exh', _('Exhibitor Pass')),
    ('pre', _('Press Pass')),
    ('jur', _('Jury Pass')),
)


class Pass(models.Model):
    order = models.CharField(_('Order'), max_length=200, unique=True)
    created = models.DateTimeField(_('Created at'), auto_now_add=True)
    seat = models.CharField(max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True)
    type = models.CharField(max_length=3, choices=PASSES_TYPES, default="vip")

    # field to control the access
    used = models.BooleanField(default=False)


INVOTATIONS_TYPES = (
    ('ina', _('Inauguration Invitation')),
    ('mad', _('MaD Facility Invitation')),
    ('thu', _('Thursday Show Invitation')),
)


class Invitation(models.Model):
    order = models.CharField(_('Order'), max_length=200, unique=True)
    created = models.DateTimeField(_('Created at'), auto_now_add=True)
    seat = models.CharField(max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True)
    type = models.CharField(max_length=3, choices=INVOTATIONS_TYPES, default="mad")

    # field to control the access
    used = models.BooleanField(default=False)


def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


post_save.connect(confirm_email, Ticket)
post_save.connect(confirm_email, MultiPurchase)
