import random
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


REG_TYPES = (
    ('invited', _('Invited')),
    ('speaker', _('Speaker')),
    ('sponsor', _('Sponsor')),
    ('regular', _('Regular')),
    ('student', _('Student'))
)

FOOD = (
    ('all', _('All')),
    ('vegetarian', _('Vegetarian')),
    ('vegan', _('Vegan'))
)

class Event(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))
    price = models.IntegerField(_('ticket price'), default=25)
    price_sponsor = models.IntegerField(_('sponsor price'), default=25)
    price_student = models.IntegerField(_('student price'), default=25)
    price_speaker = models.IntegerField(_('speaker price'), default=0)
    price_invited = models.IntegerField(_('invited price'), default=0)
    info = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)
    admin = models.EmailField(_('admin email'), blank=True, null=True)

    class Meta:
        ordering = ['-start']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('register', kwargs={'id': self.id})


class InvCode(models.Model):
    event = models.ForeignKey(Event, related_name='codes')
    code = models.CharField(_('code'), max_length=10, blank=True, null=True)
    person = models.CharField(_('for person'), max_length=100, blank=True, null=True)
    used = models.BooleanField(_('used'), default=False)

    def __str__(self):
        return self.code


class Ticket(models.Model):
    event = models.ForeignKey(Event, related_name='tickets')
    inv = models.OneToOneField(InvCode, blank=True, null=True)
    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)
    created = models.DateTimeField(_('created at'), auto_now_add=True)

    confirmed_date = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    confirm_sent = models.BooleanField(default=False)

    # Form Fields
    email = models.EmailField(_('email'))
    name = models.CharField(_('full name'), max_length=200)
    address = models.TextField(_('address'))
    org = models.CharField(_('organization'), max_length=200)
    photo = models.ImageField(_('photo'), upload_to='photos', blank=True, null=True)

    type = models.CharField(_('type'), max_length=20, choices=REG_TYPES, default='regular')
    food = models.CharField(_('food preferences'), max_length=20, choices=FOOD, default='all')
    comments = models.TextField(_('Especial needs'), blank=True, null=True)
    arrival = models.DateField(_('Arrival date'), help_text='dd/mm/YYYY')
    departure = models.DateField(_('Departure date'), help_text='dd/mm/YYYY')

    personal_info = ['email', 'name', 'address', 'org', 'photo']
    reg_info = ['type', 'food', 'comments', 'arrival', 'departure']
    form_fields = personal_info + reg_info

    def get_absolute_url(self):
        return reverse('payment', kwargs={'order': self.order})

    def gen_order_tpv(self):
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.order_tpv = timezone.now().strftime('%y%m%d')
        self.order_tpv += ''.join(random.choice(chars) for _ in range(6))
        self.save()

    def get_personal_info(self):
        pinfo = []
        for f in self.personal_info:
            field = getattr(self, f)
            name = Ticket._meta.get_field_by_name(f)[0].verbose_name
            pinfo.append({'value': field, 'name': name, 'f': f})
        return pinfo

    def get_reg_info(self):
        pinfo = []
        for f in self.reg_info:
            field = getattr(self, f)
            name = Ticket._meta.get_field_by_name(f)[0].verbose_name
            pinfo.append({'value': field, 'name': name})
        return pinfo

    def get_price(self):
        price = self.event.price
        if self.type == 'speaker':
            price = self.event.price_speaker
        elif self.type == 'sponsor':
            price = self.event.price_sponsor
        elif self.type == 'student':
            price = self.event.price_student
        elif self.type == 'invited':
            price = self.event.price_invited
        return price

    def send_reg_email(self):
        tmpl = get_template('emails/reg.txt')
        d = Context({'ticket': self})
        body = tmpl.render(d)
        email = EmailMessage(_('New Register / %s') % self.event.name,
                             body, settings.FROM_EMAIL, [self.event.admin])
        email.send(fail_silently=False)

    def send_confirm_email(self):
        # email to admin
        d = Context({'ticket': self})
        tmpl = get_template('emails/confirm.txt')
        body = tmpl.render(d)
        email = EmailMessage(_('Confirmed / %s') % self.event.name,
                             body, settings.FROM_EMAIL, [self.event.admin])
        email.send(fail_silently=False)

        # email to user
        tmpl = get_template('emails/confirm-user.txt')
        body = tmpl.render(d)
        email = EmailMessage(_('Ticket Confirmed / %s') % self.event.name,
                             body, settings.FROM_EMAIL, [self.email])
        # TODO add attachments
        email.send(fail_silently=False)

        self.confirm_sent = True
        self.save()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order


@receiver(post_save, sender=Ticket)
def confirm_email(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.confirm_sent and instance.confirmed:
        instance.send_confirm_email()


@receiver(post_save, sender=InvCode)
def gencode(sender, instance, created, raw, using, update_fields, **kwargs):
    if not instance.code:
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        instance.code = ''.join(random.choice(chars) for _ in range(10))
        instance.save()
