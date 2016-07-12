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
            reserved = order.startswith(Invitation.ORDER_START)

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


class BaseExtraData:
    def get_extra_sessions(self):
        if not self.extra_data:
            data = []
        else:
            data = json.loads(self.extra_data)
        return data

    def get_extra_session(self, pk):
        for extra in self.get_extra_sessions():
            if extra.get('session') == pk:
                return extra
        return False

    def set_extra_session_to_used(self, pk):
        data = self.get_extra_sessions()
        for extra in range(len(data)):
            if data[extra].get('session') == pk:
                data[extra]['used'] = True
                break
        self.extra_data = json.dumps(data)
        self.save()

    def save_extra_sessions(self):
        data = []
        for extra in self.session.orig_sessions.all():
           data.append({
               'session': extra.extra.id,
               'start': extra.start.strftime(settings.DATETIME_FORMAT),
               'end': extra.end.strftime(settings.DATETIME_FORMAT),
               'used': extra.used
           })
        self.extra_data = json.dumps(data)



class MultiPurchase(models.Model, BaseTicketMixing):
    ev = models.ForeignKey(Event, related_name='mps', verbose_name=_('event'))

    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)

    created = models.DateTimeField(_('created at'), auto_now_add=True)
    confirmed_date = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(_('confirmed'), default=False)
    confirm_sent = models.BooleanField(_('confirmation sent'), default=False)

    # Form Fields
    email = models.EmailField(_('email'))

    extra_data = models.TextField(_('extra data'), blank=True, null=True)

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
        verbose_name = _('multipurchase')
        verbose_name_plural = _('multipurchases')

    def __str__(self):
        return self.order


class Ticket(models.Model, BaseTicketMixing, BaseExtraData):
    session = models.ForeignKey(Session, related_name='tickets', verbose_name=_('event'))

    inv = models.OneToOneField(InvCode, blank=True, null=True, verbose_name=_('invitation code'))

    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)

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
    price = models.IntegerField(_('price'), null=True)
    tax = models.IntegerField(_('tax'), null=True)
    start = models.DateTimeField(_('start date'), null=True)
    end = models.DateTimeField(_('end date'), null=True)
    seat_layout_name = models.CharField(_('seat layout name'), max_length=200, null=True, blank=True)
    gate_name = models.CharField(_('gate name'), max_length=100, null=True, blank=True)

    # field to control the access
    used = models.BooleanField(_('used'), default=False)

    class Meta:
        ordering = ['-created']
        verbose_name = _('ticket')
        verbose_name_plural = _('tickets')

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
        self.save_extra_sessions()

    def gen_pdf(self):
        return generate_pdf(self)

    def window_code(self):
        '''
        ONLMMDDHHMM
        '''

        prefix = 'ONL'
        postfix = self.created.strftime('%m%d%H%M')
        if self.sold_in_window:
            from windows.models import TicketWindowSale
            tws = TicketWindowSale.objects.get(purchase__tickets=self)
            prefix = tws.window.code

        return prefix + postfix


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

    class Meta:
        verbose_name = _('ticket seat hold')
        verbose_name_plural = _('ticket seat holds')

    def __str__(self):
        return self.seat


class InvitationType(models.Model):
    session = models.ForeignKey(Session, related_name='invitations_types', null=True, blank=True, verbose_name=_('session'))
    name = models.CharField(_('name'), max_length=200)
    start = models.DateTimeField(_('start date'), null=True)
    end = models.DateTimeField(_('end date'), null=True)

    class Meta:
        verbose_name = _('invitation type')
        verbose_name_plural = _('invitation types')

    def __str__(self):
        return self.name


class Invitation(models.Model, BaseExtraData):
    ORDER_START = '00001'
    session = models.ForeignKey(Session, related_name='invitations', null=True, blank=True, verbose_name=_('session'))
    order = models.CharField(_('order'), max_length=200, unique=True)
    created = models.DateTimeField(_('created at'), auto_now_add=True)
    seat = models.CharField(_('seat'), max_length=20, null=True, blank=True)
    seat_layout = models.ForeignKey(SeatLayout, null=True, blank=True, verbose_name=_('seat layout'))
    type = models.ForeignKey(InvitationType, null=True, blank=True, verbose_name=_('type'))
    extra_data = models.TextField(_('extra data'), blank=True, null=True)
    is_pass = models.BooleanField(_('is pass'), default=False)

    # field to control the access
    used = models.BooleanField(_('used'), default=False)

    class Meta:
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')

    def gen_order(self, starts=''):
        """ Generate order for passes and invitations """
        if isinstance(self, Invitation):
            starts = Invitation.ORDER_START
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
        return Invitation.objects.filter(order=order).exists()

    def get_extra_data(self, key):
        data = {}
        if not self.extra_data:
            return None
        else:
            data = json.loads(self.extra_data)
        return data.get(key, None)

    def __str__(self):
        return self.order


def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


post_save.connect(confirm_email, Ticket)
post_save.connect(confirm_email, MultiPurchase)
