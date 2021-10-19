import logging

import pytest
from django.http.response import Http404

from tickets.models import Ticket
from tickets.views import get_ticket_or_404
from tickets.factories import TicketFactory


@pytest.mark.django_db
def test_get_ticket_error(caplog):
    caplog.set_level(logging.INFO)

    with pytest.raises(Http404):
        get_ticket_or_404(order_tpv='2110999834')


@pytest.mark.django_db
def test_get_ticket_ok():
    ticket_db = TicketFactory()

    ticket = get_ticket_or_404(order_tpv=ticket_db.order_tpv)
    assert isinstance(ticket, Ticket)
