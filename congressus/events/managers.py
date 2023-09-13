from django.db import models


class EventQuerySet(models.QuerySet):
    def with_templates(self):
        return self.select_related(
            "session",
            "session__template",
            "session__window_template",
            "session__space",
            "session__space__event",
            "seat_layout",
        )


class ReadEventManager(models.Manager):
    def get_queryset(self):
        return EventQuerySet(self.model, using="default")

    def choices(self) -> list[tuple[str, str]]:
        choices = []
        for event in self.get_queryset().order_by("-id").values("id", "name"):
            choices.append((str(event["id"]), event["name"]))
        return choices


class WriteEventManager(models.Manager):
    def get_queryset(self):
        return EventQuerySet(self.model, using="default")
