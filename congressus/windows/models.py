from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from autoslug import AutoSlugField

from events.models import Event


class TicketWindow(models.Model):
    event = models.ForeignKey(Event, related_name='windows')

    name = models.CharField(_('name'), max_length=200)
    slug = AutoSlugField(populate_from='name')

    # users that can login to this window
    users = models.ManyToManyField(User, related_name='windows', blank=True)
    location = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.slug
