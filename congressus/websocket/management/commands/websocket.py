from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from websocket.server import WSServer


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = WSServer()
        s.run()
