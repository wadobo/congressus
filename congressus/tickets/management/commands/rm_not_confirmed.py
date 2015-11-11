from django.core.management.base import BaseCommand, CommandError
from tickets.models import Ticket
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    def handle(self, *args, **options):
        d = timezone.now() - timedelta(seconds=3600)
        Ticket.objects.filter(confirmed=False, created__lt=d).delete()

