from django.core.management.base import BaseCommand, CommandError
from tickets.models import MultiPurchase
from windows.utils import online_sale


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('event')

    def handle(self, *args, **options):
        event = options['event']
        mps = MultiPurchase.objects.filter(ev__slug=event, confirmed=True)
        mps = mps.filter(sales=None, tickets__sold_in_window=False).distinct()

        for tk in mps:
            online_sale(tk)
