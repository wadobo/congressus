import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from websocket.server import WSServer
from threading import Timer
from tickets.models import TicketSeatHold


def clean_holds(ws):
    d = (timezone.now() - datetime.timedelta(seconds=5 * 60))
    holds = TicketSeatHold.objects.filter(date__lt=d)
    for hold in holds:
        ws.drop_seat(hold)
    t = Timer(60, clean_holds, [ws])
    t.start()


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = WSServer()
        clean_holds(s)
        s.run()
