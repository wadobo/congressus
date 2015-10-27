from django.db import models
from django.utils.translation import ugettext_lazy as _


class Event(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    start = models.DateTimeField(_('start date'))
    end = models.DateTimeField(_('end date'))
    price = models.IntegerField(_('ticket price'), default=25)
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
    name = models.CharField(_('name'), max_length=200)
    surname = models.CharField(_('surname'), max_length=200)
    org = models.CharField(_('organization'), max_length=200)
    email = models.EmailField(_('email'))

    form_fields = ['name', 'surname', 'org', 'email']

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.order
