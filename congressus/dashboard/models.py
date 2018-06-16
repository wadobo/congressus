from autoslug import AutoSlugField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from events.models import Event


CHARTS = (
    ('os_c', _('Online sales chart')),
    ('ws_c', _('Window sales chart')),
    ('a_c', _('Access chart')),
    ('os_p', _('Online sales pie')),
    ('ws_p', _('Window sales pie')),
    ('a_p', _('Access pie')),
    ('ws_b', _('Window sales bar')),
)
TIMESTEPS = (
    ('daily', _('daily')),
    ('hourly', _('hourly')),
    ('minly', _('each minute')),
)
NUM_COLS = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('6', '6')
)

class ConfigChart(models.Model):
    type = models.CharField(_('type'), max_length=8, choices=CHARTS, default="os_c")
    timestep = models.CharField(_('time step'), max_length=10, choices=TIMESTEPS, default="daily")
    max_steps = models.IntegerField(_('maximum steps'), default=10)

    def __str__(self):
        return "%s: %s - %d" % (self.type, self.timestep, self.max_steps)


class Dashboard(models.Model):
    event = models.ForeignKey(Event, verbose_name=_('event'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=200)
    num_cols = models.CharField(_("number columns"), max_length=2, choices=NUM_COLS, default="2")
    slug = AutoSlugField(populate_from='name')
    charts = models.ManyToManyField(ConfigChart)
