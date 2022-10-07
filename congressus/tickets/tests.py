import pytest
from unittest.mock import patch

from django.test import Client
from django.urls import reverse

import tickets.utils
import tickets.views
from events.factories import EventFactory, TicketTemplateFactory
from tickets.factories import MultiPurchaseFactory
from tickets.models import MultiPurchase
from windows.factories import TicketWindowFactory, TicketWindowSaleFactory
from windows.models import TicketWindowSale


@pytest.mark.django_db
def test_ticket_thanks_template_from_window_ticket():
    event = EventFactory.build()
    mp = MultiPurchaseFactory.build(ev=event, confirmed=True)
    ticket_template = TicketTemplateFactory.build(id=1, is_html_format=False)
    ticket_window = TicketWindowFactory.build(event=event)
    pf = 1
    ticket_window_sale = TicketWindowSaleFactory.build(pk=pf, purchase=mp, window=ticket_window)

    with (
        patch.object(tickets.views, "get_ticket_or_404", return_value=mp),
        patch.object(MultiPurchase, "get_first_ticket_window_sale", return_value=ticket_window_sale),
        patch.object(tickets.utils, "get_ticket_template", return_value=ticket_template),
        patch.object(TicketWindowSale, "get_first_template", return_value=ticket_template),
        patch.object(MultiPurchase, "generate_pdf", return_value=None) as mock,
    ):
        client = Client()
        response = client.post(reverse('thanks', kwargs={"order": mp.order }), {"ticket": mp.order})
        assert response.status_code == 200
        mock.assert_called_with(ticket_template)
