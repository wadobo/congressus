from django.db import models
from django.db.models import Prefetch


class EventQuerySet(models.QuerySet):
    def with_amount_sold_tickets(self):
        return self.annotate(
            amount_sold_tickets=models.Count(
                "spaces__sessions__tickets",
                filter=models.Q(spaces__sessions__tickets__confirmed=True),
            )
        )

    def with_sessions(self):
        return self.prefetch_related("spaces__sessions")

    def with_access(self):
        return self.prefetch_related("access")


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


class SessionQuerySet(models.QuerySet):
    def with_space(self):
        return self.select_related("space", "space__event")

    def with_seat_layouts(self):
        return self.prefetch_related("space__seat_map__layouts")

    def with_seat_holds(self):
        from tickets.models import TicketSeatHold

        return self.prefetch_related(
            Prefetch("seat_holds", TicketSeatHold.objects.select_related("layout"))
        )

    def with_tickets(self):
        return self.prefetch_related("tickets")

    def with_invitations(self):
        from invs.models import InvitationType, Invitation, InvUsedInSession

        return self.prefetch_related(
            Prefetch(
                "invitation_types",
                InvitationType.objects.prefetch_related(
                    Prefetch(
                        "invitations",
                        Invitation.objects.select_related(
                            "seat_layout"
                        ).prefetch_related(
                            Prefetch(
                                "usedin",
                                InvUsedInSession.objects.select_related("session"),
                            )
                        ),
                    ),
                ),
            ),
        )

    def get_sessions_dict(self) -> dict[int, str]:
        sessions = self.select_related("space").values("id", "name", "space__name")
        return {
            session["id"]: f"{session['space__name']} - {session['name']}"
            for session in sessions
        }


class ReadSessionManager(models.Manager):
    def get_queryset(self):
        return SessionQuerySet(self.model, using="default")


class WriteSessionManager(models.Manager):
    def get_queryset(self):
        return SessionQuerySet(self.model, using="default")
