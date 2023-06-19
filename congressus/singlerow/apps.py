from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SinglerowConfig(AppConfig):
    name = 'singlerow'
    verbose_name = _('Single Row')
