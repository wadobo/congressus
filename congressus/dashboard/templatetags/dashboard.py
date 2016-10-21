from django import template
from django.utils.translation import ugettext as _
from django.utils.html import mark_safe

from django.db.models import Count
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Sum
from django.db.models import Value


from tickets.models import Ticket


register = template.Library()


def filter_tickets(event, space=None, sessions=None, windows=None,
                   sdate=None, edate=None):
    tickets = Ticket.objects.filter(confirmed=True, session__space__event=event)
    if space:
        tickets = tickets.filter(session__space=space)
    if sessions:
        tickets = tickets.filter(session__in=sessions)
    if windows:
        tickets = tickets.filter(mp__sales__window__in=windows)
    if sdate:
        tickets = tickets.filter(created__gte=sdate)
    if edate:
        tickets = tickets.filter(created__lte=edate)

    return tickets


@register.simple_tag
def db_count(event, **kwargs):
    tickets = filter_tickets(event, **kwargs)
    return tickets.count()

@register.simple_tag
def db_prices(event, **kwargs):
    tickets = filter_tickets(event, **kwargs)
    tickets = tickets.aggregate(total_price=Sum('price'),
                    price_without_iva=Sum(F('price')/(1+F('tax')/100.0), output_field=FloatField()))
    if tickets and tickets['total_price']:
        return '{total_price:.2f} / {price_without_iva:.2f}'.format(**tickets)

    return '--'
