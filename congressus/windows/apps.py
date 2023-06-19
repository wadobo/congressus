from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WindowsConfig(AppConfig):
    name = 'windows'
    verbose_name = _('Windows')
