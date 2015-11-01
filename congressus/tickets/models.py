import random
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.core.urlresolvers import reverse


REG_TYPES = (
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
    info = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)
    admin = models.EmailField(_('admin email'), blank=True, null=True)

    class Meta:
        ordering = ['-start']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('register', kwargs={'id': self.id})


class Ticket(models.Model):
    event = models.ForeignKey(Event, related_name='tickets')
    order = models.CharField(_('order'), max_length=200, unique=True)
    order_tpv = models.CharField(_('order TPV'), max_length=12, blank=True, null=True)
    created = models.DateTimeField(_('created at'), auto_now_add=True)

    confirmed_date = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    confirmed = models.BooleanField(default=False)

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
        return price

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order
