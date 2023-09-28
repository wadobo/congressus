from django.db import models


class AccessControlQuerySet(models.QuerySet):
    def with_event(self):
        return self.select_related("event")

    def with_gates(self):
        return self.prefetch_related("event__gates")


class ReadAccessControlManager(models.Manager):
    def get_queryset(self):
        return AccessControlQuerySet(self.model, using="default")


class WriteAccessControlManager(models.Manager):
    def get_queryset(self):
        return AccessControlQuerySet(self.model, using="default")
