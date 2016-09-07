from django.core.management.base import BaseCommand, CommandError
from tickets.models import TicketSeatHold
from events.models import Session
from events.models import SeatLayout
from events.models import Event


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-s', '--session')
        parser.add_argument('event')
        parser.add_argument('layout')
        parser.add_argument('row1:row2')
        parser.add_argument('col1:col2')

    def handle(self, *args, **options):
        event = options['event']
        layout = options['layout']
        r1, r2 = options['row1:row2'].split(':')
        c1, c2 = options['col1:col2'].split(':')
        session = options.get('session', '')

        layout = SeatLayout.objects.get(name=layout)
        event = Event.objects.get(slug=event)

        if session:
            sessions = Session.objects.filter(pk=session)
        else:
            sessions = Session.objects.filter(space__event=event, space__numbered=True)

        for s in sessions:
            for r in range(int(r1), int(r2)+1):
                for c in range(int(c1), int(c2)+1):
                    print(layout, r, c)
                    tsh = TicketSeatHold(type="R",
                                         client="ADMIN",
                                         session=s,
                                         layout=layout,
                                         seat='{}-{}'.format(r, c))
                    tsh.save()
