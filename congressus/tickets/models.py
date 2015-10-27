from django.db import models
from django.utils.translation import ugettext_lazy as _


REG_TYPES = (
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
    info = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    event = models.ForeignKey(Event, related_name='tickets')
    order = models.CharField(_('order'), max_length=200, unique=True)
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

    form_fields = ['email', 'name', 'address', 'org', 'photo',
                   'type', 'food', 'comments', 'arrival', 'departure']

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order
