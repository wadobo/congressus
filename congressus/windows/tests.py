import pytest
from unittest.mock import patch

from django.test import Client
from django.urls import reverse

import tickets.utils
from events.factories import EventFactory
from events.factories import TicketTemplateFactory
from tickets.factories import MultiPurchaseFactory
from tickets.models import MultiPurchase
from windows.factories import TicketWindowFactory
from windows.views import WindowTicket


@pytest.mark.django_db
def test_ticket_window_old_format():
    event = EventFactory.build()
    mp = MultiPurchaseFactory.build(ev=event)
    ticket_window = TicketWindowFactory.build(event=event)
    ticket_template = TicketTemplateFactory.build(id=1, is_html_format=False)

    with (
        patch.object(WindowTicket, "get_mp", return_value=mp) as mock1,
        patch.object(WindowTicket, "get_window", return_value=ticket_window) as mock2,
        patch.object(WindowTicket, "test_func", return_value=True) as mock3,
        patch.object(tickets.utils, "get_ticket_template", return_value=ticket_template) as mock4,
        patch.object(MultiPurchase, "generate_pdf", return_value=False) as mp_mock,

    ):

        client = Client()
        response = client.get(reverse('window_ticket', kwargs={
            "ev": event.slug,
            "w": ticket_window.slug,
            "pf": ticket_template.id,
            "order": mp.order,
        }))
        assert response.status_code == 200
        mp_mock.assert_called_with(ticket_template)


@pytest.mark.django_db
def test_ticket_window_new_format():
    event = EventFactory.build()
    mp = MultiPurchaseFactory.build(ev=event)
    ticket_window = TicketWindowFactory.build(event=event)
    ticket_template = TicketTemplateFactory.build(id=1, is_html_format=True)

    with (
        patch.object(WindowTicket, "get_mp", return_value=mp) as mock1,
        patch.object(WindowTicket, "get_window", return_value=ticket_window) as mock2,
        patch.object(WindowTicket, "test_func", return_value=True) as mock3,
        patch.object(tickets.utils, "get_ticket_template", return_value=ticket_template) as mock4,
        patch.object(MultiPurchase, "generate_html", return_value=False) as mp_mock,

    ):

        client = Client()
        response = client.get(reverse('window_ticket', kwargs={
            "ev": event.slug,
            "w": ticket_window.slug,
            "pf": ticket_template.id,
            "order": mp.order,
        }))
        assert response.status_code == 200
        mp_mock.assert_called_with(ticket_template)
