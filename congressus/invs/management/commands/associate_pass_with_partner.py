import csv
from django.core.management.base import BaseCommand, CommandError

from invs.models import Invitation


class Command(BaseCommand):
    help = '''Load csv file with orders and names for associate. '''
    
    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)


    def handle(self, *args, **options):
        filename = options['filename']

        if not filename:
            return "Any csv file"

        with open(filename, 'r') as f:
            rows = list(csv.reader(f, delimiter=','))

        total = len(rows)
        for code, name in rows:
            try:
                invs = Invitation.objects.get(order=code, is_pass=True)
            except:
                print("Not found order: {0}".format(code))
                total -= 1
                continue
            invs.name = name
            invs.save()
        print("Associate {0}/{1} partners".format(total, len(rows)))
