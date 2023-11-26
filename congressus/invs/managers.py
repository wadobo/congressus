from django.db import models
from django.db.models import Prefetch


class InvitationQuerySet(models.QuerySet):
    def with_sessions(self):
        from invs.models import InvUsedInSession

        return self.select_related(
            "type",
            # "type__event",
            "seat_layout",
        ).prefetch_related(
            "type__sessions",
            "type__gates",
            Prefetch("usedin", InvUsedInSession.objects.select_related("session")),
        )


class ReadInvitationManager(models.Manager):
    def get_queryset(self):
        return InvitationQuerySet(self.model, using="default")


class WriteInvitationManager(models.Manager):
    def get_queryset(self):
        return InvitationQuerySet(self.model, using="default")
