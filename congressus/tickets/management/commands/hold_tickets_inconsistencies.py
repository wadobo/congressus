from django.core.management.base import BaseCommand, CommandError
from tickets.models import Ticket
from tickets.models import TicketSeatHold
from windows.utils import online_sale


class Command(BaseCommand):

    def handle(self, *args, **options):
        tickets = Ticket.objects.filter(confirmed=True, seat__isnull=False)
        # some tickets not appear in seatHold
        total = len(tickets)
        problems = 0
        repeats = 0
        for t in tickets:
            session = t.session
            layout = t.seat_layout
            seat = t.seat
            repeat = tickets.filter(session=session, seat_layout=layout, seat=seat).exclude(id=t.id)
            if repeat.exists():
                repeats += len(repeat)
                print("REPEAT SEAT", t.id, [r.id for r in repeat])
            tsh = TicketSeatHold.objects.filter(type='R', session=session, layout=layout, seat=seat)
            if len(tsh) < 1:
                print("NO HOLD TICKET {0}: {1} {2} {3}".format(t.order, session, layout, seat))
                problems += 1
            elif len(tsh) > 1:
                print("DUPLICATED", tsh)
        print("====================")
        print("Repeats {0} tickets of {1}".format(int(repeats/2), total))
        print("Problems in {0} tickets of {1}".format(problems, total))
