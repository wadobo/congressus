import random
import json
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import get_template
from django.template import Context

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.urlresolvers import reverse

from events.models import Event, InvCode
from events.models import Session


REG_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('regular', _('Regular')),
    ('student', _('Student'))
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

    def gen_order_tpv(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.order_tpv = timezone.now().strftime('%y%m%d')
        self.order_tpv += ''.join(random.choice(chars) for _ in range(6))
        self.save()

    def get_price(self):
        # TODO manage ticket type
        return self.session.price

    def send_reg_email(self):
        tmpl = get_template('emails/reg.txt')
        d = Context({'ticket': self})
        body = tmpl.render(d)
        email = EmailMessage(_('New Register / %s') % self.event(),
                             body, settings.FROM_EMAIL, [self.event().admin])
        email.send(fail_silently=False)

    def send_confirm_email(self):
        # email to admin
        d = Context({'ticket': self})
        tmpl = get_template('emails/confirm.txt')
        body = tmpl.render(d)
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
            body = tmpl.render(d)

        body = body.replace('TICKETID', self.order)

        email = EmailMessage(subject, body, settings.FROM_EMAIL, [self.email])

        if e:
            # adding attachments
            for att in e.attachs.all():
                email.attach_file(att.attach.path)

        email.send(fail_silently=False)

        self.confirm_sent = True
        self.save()

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

    def confirm(self):
        self.confirmed = True
        self.confirmed_date = timezone.now()
        for t in self.tickets.all():
            t.confirmed = True
            t.confirmed_date = timezone.now()
        self.save()

    def is_mp(self):
        return True

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

    # Form Fields
    email = models.EmailField(_('Email'))

    extra_data = models.TextField(blank=True, null=True)

    mp = models.ForeignKey(MultiPurchase, related_name='tickets', null=True, blank=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order


def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


post_save.connect(confirm_email, Ticket)
post_save.connect(confirm_email, MultiPurchase)
