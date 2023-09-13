from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from tickets.models import MultiPurchase


class TicketWindowSaleQuerySet(models.QuerySet):
    pass


class WriteTicketWindowSaleManager(models.Manager):
    def get_queryset(self):
        return TicketWindowSaleQuerySet(self.model, using="default")

    def create_from_mp(self, mp: "MultiPurchase"):
        from windows.models import TicketWindow

        online_window = TicketWindow.objects.filter(event=mp.ev, online=True).first()
        if not online_window:
            return

        price = mp.get_price()
        payed = mp.get_price()
        sale, created = self.get_or_create(
            purchase=mp, window=online_window, price=price, payed=payed, payment="card"
        )
        sale.save()

    def create_from_mp2(self, mp: "MultiPurchase"):
        pass
