from django.db import models


class MultiPurchaseQuerySet(models.QuerySet):
    def with_tickets(self):
        return self.prefetch_related("tickets")

    def with_ticket_templates(self):
        from tickets.models import Ticket

        return self.prefetch_related(
            models.Prefetch(
                "tickets",
                queryset=Ticket.objects.select_related(
                    "session",
                    "session__template",
                    "session__window_template",
                    "session__space",
                    "session__space__event",
                    "seat_layout",
                ),
            ),
        )

    def with_price(self):
        from tickets.models import Ticket

        return (
            self.select_related("discount")
            .prefetch_related(
                models.Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related("session"),
                ),
            )
            .annotate(
                total_price1=models.Sum(
                    models.Case(
                        models.When(
                            discount__isnull=True,
                            then=models.F("tickets__price"),
                        ),
                        models.When(
                            discount__type="percent",
                            then=models.F("tickets__price")
                            * (1 - models.F("discount__value") / 100),
                        ),
                        models.When(
                            discount__type="amount",
                            then=models.F("tickets__price")
                            - models.F("discount__value"),
                        ),
                        default=models.F("tickets__price"),
                        output_field=models.DecimalField(decimal_places=2),
                    )
                )
            )
        )

    def has_conflict_in_space(self) -> bool:
        from tickets.models import Ticket

        distinct_spaces = (
            self.prefetch_related(
                models.Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related("session"),
                ),
            )
            .values("tickets__session__space")
            .annotate(distinct_session=models.Count("tickets__session__space"))
        )
        return len(distinct_spaces) > 1

    def has_conflict_in_session(self) -> bool:
        distinct_sessions = (
            self.prefetch_related("tickets")
            .values("tickets__session")
            .annotate(total=models.Count("tickets__session"))
        )
        return len(distinct_sessions) > 1


class ReadMultiPurchaseManager(models.Manager):
    def get_queryset(self):
        return MultiPurchaseQuerySet(self.model, using="default")


class WriteMultiPurchaseManager(models.Manager):
    def get_queryset(self):
        return MultiPurchaseQuerySet(self.model, using="default")


class TicketQuerySet(models.QuerySet):
    def with_templates(self):
        return self.select_related(
            "session",
            "session__template",
            "session__window_template",
            "session__space",
            "session__space__event",
            "seat_layout",
        )


class ReadTicketManager(models.Manager):
    def get_queryset(self):
        return TicketQuerySet(self.model, using="default")


class WriteTicketManager(models.Manager):
    def get_queryset(self):
        return TicketQuerySet(self.model, using="default")
