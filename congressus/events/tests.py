import pytest

from events.choices import SessionTemplate
from events.factories import TicketTemplateFactory
from tickets.factories import TicketFactory


@pytest.mark.django_db
def test_preview_horizontal():
    ticket_template = TicketTemplateFactory(
        name='thermal',
        pagesize_width=17.64,
        pagesize_height=8.01,
        left_margin=0,
        right_margin=0,
        bottom_margin=0,
        top_margin=1.76,
    )

    ticket = TicketFactory(session__template=ticket_template)
    ticket.pdf_format(session_template=SessionTemplate.ONLINE)


@pytest.mark.django_db
def test_preview_vertical():
    ticket_template = TicketTemplateFactory(
        name='vertical',
        pagesize_width=7.64,
        pagesize_height=81.01,
        left_margin=0,
        right_margin=0,
        bottom_margin=0,
        top_margin=1.76,
    )

    ticket = TicketFactory(session__template=ticket_template)
    ticket.pdf_format(session_template=SessionTemplate.ONLINE)
