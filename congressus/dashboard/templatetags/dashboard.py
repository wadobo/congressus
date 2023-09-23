from django import template
from django.utils.translation import gettext as _

from django.db.models import F
from django.db.models import FloatField
from django.db.models import Sum
from django.contrib.humanize.templatetags.humanize import intcomma


from tickets.models import Ticket
from windows.models import TicketWindowCashMovement


register = template.Library()


def filter_tickets(
    event,
    space=None,
    sessions=None,
    windows=None,
    sdate=None,
    edate=None,
    days=None,
    session=None,
):
    kw = {
        "confirmed": True,
        "session__space__event": event,
    }
    if space:
        kw["session__space"] = space
    if sessions:
        kw["session__in"] = sessions
    if session:
        kw["session"] = session
    if windows:
        kw["mp__sales__window__in"] = windows
    if sdate:
        kw["created__gte"] = sdate
    if edate:
        kw["created__lte"] = edate
    if days:
        kw["created__date__in"] = days

    return Ticket.objects.filter(**kw)


@register.simple_tag
def db_count(event, **kwargs):
    tickets = filter_tickets(event, **kwargs)
    return intcomma(len(tickets))


@register.simple_tag
def db_prices(event, **kwargs):
    tickets = filter_tickets(event, **kwargs)
    tickets = tickets.aggregate(
        total_price=Sum("price"),
        price_without_tax=Sum(
            F("price") / (1 + F("tax") / 100.0), output_field=FloatField()
        ),
    )
    if tickets and tickets["total_price"]:
        tax = intcomma("{total_price:.2f}".format(**tickets))
        notax = intcomma("{price_without_tax:.2f}".format(**tickets))
        return "{0} / {1}".format(tax, notax)

    return "--"


@register.simple_tag
def db_window_total(event, **kwargs):
    tickets = filter_tickets(event, **kwargs)
    tickets = tickets.aggregate(
        total_price=Sum("price"),
        price_without_tax=Sum(
            F("price") / (1 + F("tax") / 100.0), output_field=FloatField()
        ),
    )
    if tickets and tickets["total_price"]:
        return tickets["total_price"]

    return "--"


@register.simple_tag
def db_window_movements_total(movements):
    mtotal = 0
    for m in movements:
        if m.type == "change":
            mtotal -= m.amount
        else:
            mtotal += m.amount
    return mtotal


@register.simple_tag
def db_window_count_total(total, mtotal):
    try:
        total = float(total)
        mtotal = float(mtotal)
    except Exception:
        return "--"
    return mtotal - total


@register.simple_tag
def db_window_movements(window, days=None):
    # window movements and one more for credit card sales
    movements = window.movements.all()
    if days:
        movements = movements.filter(date__date__in=days)
    credit_mov = TicketWindowCashMovement(window=window)
    credit_mov.type = _("Credit card sale")

    tickets = filter_tickets(window.event, windows=[window])
    if days:
        tickets = tickets.filter(created__date__in=days)
    tickets = tickets.filter(mp__sales__payment="card").aggregate(
        total_price=Sum("price")
    )
    if tickets and tickets["total_price"]:
        credit_mov.amount = tickets["total_price"]
    movements = list(movements) + [credit_mov]
    return movements
