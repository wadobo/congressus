from django.core.management.base import BaseCommand, CommandError
from tickets.models import Ticket
from invs.models import Invitation

import multiprocessing


class Command(BaseCommand):
    def handle(self, *args, **options):

        p1 = multiprocessing.Process(target=self.refill_tickets)
        p1.start()

        p2 = multiprocessing.Process(target=self.refill_invs)
        p2.start()

        p1.join()
        p2.join()

    def refill_tickets(self):
        tks = Ticket.objects.filter(confirmed=True, used=False, extra_data__isnull=False)
        c = tks.count()
        for i, tk in enumerate(tks):
            print("tk {}/{} ".format(i, c))
            tk.save_extra_sessions()
            tk.save()

    def refill_invs(self):
        invs = Invitation.objects.filter(extra_data__isnull=False)
        c = invs.count()
        for i, inv in enumerate(invs):
            print("inv {}/{} ".format(i, c))
            inv.save_extra_sessions()
            inv.save()
