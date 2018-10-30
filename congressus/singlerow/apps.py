from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SinglerowConfig(AppConfig):
    name = 'singlerow'
    verbose_name = _('Single Row')
