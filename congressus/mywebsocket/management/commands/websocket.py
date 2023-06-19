import datetime
from threading import Timer

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import connection
from django.utils import timezone

from mywebsocket.server import WSServer
from tickets.models import TicketSeatHold


def clean_holds(ws):
    time_h = (timezone.now() - datetime.timedelta(seconds=settings.EXPIRED_SEAT_H))
    time_c = (timezone.now() - datetime.timedelta(seconds=settings.EXPIRED_SEAT_C))
    time_p = (timezone.now() - datetime.timedelta(seconds=settings.EXPIRED_SEAT_P))
    query = Q(date__lt=time_h, type="H") | Q(date__lt=time_c, type="C") | Q(date__lt=time_p, type="P")
    holds = TicketSeatHold.objects.filter(query)
    for hold in holds:
        ws.drop_seat(hold)

    ws.notify_confirmed()
    t = Timer(60, clean_holds, [ws])
    t.start()

    connection.close()


class Command(BaseCommand):
    help = 'Start websocket server'

    def add_arguments(self, parser):
        parser.add_argument('--port', action='store', type=int, default=9007)

    def handle(self, *args, **options):
        s = WSServer(port=options.get('port'))
        clean_holds(s)
        s.run()
