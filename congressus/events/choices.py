from django.db import models
from django.utils.translation import gettext_lazy as _


class SessionTemplate(models.TextChoices):
    WINDOW = "WIN", _("Ticket window")
    ONLINE = "ONL", _("Online")
