from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InvsConfig(AppConfig):
    name = 'invs'
    verbose_name = _('Invitations')
