from django.core.management.base import BaseCommand
from tickets.models import Ticket
from tickets.models import TicketSeatHold


class Command(BaseCommand):
    def handle(self, *args, **options):
        tickets = Ticket.objects.filter(
            confirmed=True, seat__isnull=False
        ).select_related("session", "seat_layout")

        tickets_sh = TicketSeatHold.objects.filter(type="R").select_related(
            "session", "layout"
        )
        # some tickets not appear in seatHold
        total = len(tickets)
        problems = 0
        repeats = 0
        for t in tickets:
            session = t.session
            layout = t.seat_layout
            seat = t.seat
            repeat = [
                _t
                for _t in tickets
                if _t.session == session
                and _t.seat_layout == layout
                and _t.seat == seat
                and _t.id != t.id
            ]
            if len(repeat) >= 1:
                repeats += len(repeat)
                print("REPEAT SEAT", t.id, [r.id for r in repeat])
            tsh = [
                sh
                for sh in tickets_sh
                if sh.session == session and sh.layout == layout and sh.seat == seat
            ]
            if len(tsh) < 1:
                print(
                    "NO HOLD TICKET {0}: {1} {2} {3}".format(
                        t.order, session, layout, seat
                    )
                )
                problems += 1
            elif len(tsh) > 1:
                print("DUPLICATED", tsh)
        print("====================")
        print("Repeats {0} tickets of {1}".format(int(repeats / 2), total))
        print("Problems in {0} tickets of {1}".format(problems, total))
