from django.core.management.base import BaseCommand, CommandError
from tickets.models import Ticket
from invs.models import Invitation
from events.models import Event

import multiprocessing


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('event', nargs='?', type=str)

    def handle(self, *args, **options):
        self.event = options.get('event')

        p1 = multiprocessing.Process(target=self.refill_tickets)
        p1.start()

        p2 = multiprocessing.Process(target=self.refill_invs)
        p2.start()

        p1.join()
        p2.join()

    def refill_tickets(self):
        tks = Ticket.objects.filter(confirmed=True, used=False, extra_data__isnull=False)

        if self.event:
            ev = Event.objects.get(slug=self.event)
            tks = tks.filter(session__space__event=ev)

        c = tks.count()
        for i, tk in enumerate(tks):
            print("tk {}/{} ".format(i, c))
            tk.save_extra_sessions()
            tk.save()

    def refill_invs(self):
        print (self.event)
        invs = Invitation.objects.filter(type__sessions__orig_sessions__isnull=False)

        if self.event:
            ev = Event.objects.get(slug=self.event)
            invs = invs.filter(type__event=ev)

        c = invs.count()
        for i, inv in enumerate(invs):
            print("inv {}/{} ".format(i, c))
            inv.save_extra_sessions()
            inv.save()
