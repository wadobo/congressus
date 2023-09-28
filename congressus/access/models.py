from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from access.managers import ReadAccessControlManager, WriteAccessControlManager

from events.models import Event


class AccessControl(models.Model):
    event = models.ForeignKey(
        Event, related_name="access", verbose_name=_("event"), on_delete=models.CASCADE
    )

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(unique=True)

    location = models.CharField(_("location"), max_length=500, blank=True, null=True)
    mark_used = models.BooleanField(_("mark used"), default=True)

    read_objects = ReadAccessControlManager()
    objects = WriteAccessControlManager()

    class Meta:
        verbose_name = _("access control point")
        verbose_name_plural = _("access control points")

    def __str__(self):
        return self.name

    def checked_today(self, date, status=None):
        if not date:
            date = timezone.now()
        today = self.log_access.filter(
            date__year=date.year, date__month=date.month, date__day=date.day
        )
        if status:
            today = today.filter(status=status)
        return today.count()


AC_TYPES = (
    ("ok", _("ok")),
    ("right", _("ok")),
    ("wrong", _("wrong")),
    ("incorrect", _("incorrect")),
    ("used", _("used")),
    ("maybe", _("maybe")),
)


class LogAccessControl(models.Model):
    access_control = models.ForeignKey(
        AccessControl,
        related_name="log_access",
        verbose_name=_("access control"),
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        _("status"), max_length=10, choices=AC_TYPES, default="right"
    )

    class Meta:
        verbose_name = _("access control point log")
        verbose_name_plural = _("access control point logs")
