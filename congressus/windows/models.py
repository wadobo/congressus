from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from autoslug import AutoSlugField

from events.models import Event
from tickets.models import MultiPurchase


PAYMENT_TYPES = (
    ('cash', _('Cash')),
    ('card', _('Credit Card')),
)


class TicketWindow(models.Model):
    event = models.ForeignKey(Event, related_name='windows')

    name = models.CharField(_('name'), max_length=200)
    slug = AutoSlugField(populate_from='name')

    location = models.CharField(max_length=500, blank=True, null=True)

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
