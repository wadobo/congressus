import logging
from unittest.mock import patch

import pytest

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.http.response import Http404

import tickets.utils
import tickets.views
from events.choices import SessionTemplate
from events.factories import SeatLayoutFactory
from events.factories import SessionFactory
from tickets.factories import MultiPurchaseFactory, TicketFactory
from tickets.models import MultiPurchase, Ticket
from tickets.models import TicketSeatHold
from tickets.views import get_ticket_or_404
from windows.factories import TicketWindowFactory, TicketWindowSaleFactory


@pytest.mark.django_db
def test_get_ticket_error(caplog):
    caplog.set_level(logging.INFO)

    with pytest.raises(Http404):
        get_ticket_or_404(order_tpv="2110999834")


@pytest.mark.django_db
def test_get_ticket_ok():
    ticket_db = TicketFactory()

    ticket = get_ticket_or_404(order_tpv=ticket_db.order_tpv)
    assert isinstance(ticket, Ticket)


@pytest.mark.django_db
def test_ticket_thanks_template_from_window_ticket():
    ticket = TicketFactory.create()
    ticket_window = TicketWindowFactory.create(event=ticket.mp.ev)
    TicketWindowSaleFactory.create(purchase=ticket.mp, window=ticket_window)

    with (
        patch.object(tickets.views, "get_ticket_or_404", return_value=ticket.mp),
        patch.object(Ticket, "get_template") as mock,
    ):
        client = Client()
        response = client.post(
            reverse("thanks", kwargs={"order": ticket.mp.order}),
            {"ticket": ticket.mp.order},
        )
        assert response.status_code == 200
        mock.assert_called_once_with(SessionTemplate.ONLINE)


@pytest.mark.django_db
def test_remove_mp_from_admin_should_free_seat():
    session = SessionFactory(space__numbered=True)
    seat_layout = SeatLayoutFactory(
        map=session.space.seat_map,
        gate__event=session.space.event,
    )
    mp = MultiPurchaseFactory(ev=session.space.event, confirmed=False)
    TicketFactory(mp=mp, session=session, seat_layout=seat_layout, seat="1-1")
    ticket_hold = TicketSeatHold(
        session=session,
        layout=seat_layout,
        seat="1-1",
        type="R",
    )
    ticket_hold.save()

    # Seat busy
    assert MultiPurchase.objects.count() == 1
    assert session.is_seat_available(seat_layout.id, "1", "1") is False

    delete_confirmation_data = {
        ACTION_CHECKBOX_NAME: mp.pk,
        "action": "delete_selected",
        "post": "yes",
    }
    client = Client()
    superuser = User.objects.create_superuser(
        username="super",
        password="secret",
        email="super@example.com",
    )
    client.force_login(superuser)

    url = reverse("admin:tickets_multipurchase_changelist")
    response = client.post(url, delete_confirmation_data, follow=True)
    assert response.status_code == 200

    # Seat free
    assert MultiPurchase.objects.count() == 0
    assert session.is_seat_available(seat_layout.id, "1", "1") is True
