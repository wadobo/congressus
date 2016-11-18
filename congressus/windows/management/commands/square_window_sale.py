from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from datetime import date
from windows.models import TicketWindow
from windows.models import TicketWindowSale
from windows.models import TicketWindowCashMovement


class Command(BaseCommand):

    def handle(self, *args, **options):
        today = date.today()
        for window_sale in TicketWindow.objects.all():
            out = TicketWindowSale.objects.filter(window=window_sale, payment='cash', date__date=today).aggregate(tprice=Sum('price'))
            cash = out.get('tprice', 0)
            cash = 0 if not cash else cash

            movements = TicketWindowCashMovement.objects.filter(window=window_sale, date__date=today)
            for mov in movements:
                cash += mov.signed_amount()
            window_sale.cash = cash
            window_sale.save()

            print("total en taquilla {0}: {1}".format(window_sale.slug, cash))
