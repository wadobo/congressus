import pytest

from invs.factories import InvitationFactory
from tickets.factories import MultiPurchaseFactory, TicketFactory


@pytest.mark.parametrize(
    "baseticket_factory", [TicketFactory, MultiPurchaseFactory, InvitationFactory]
)
@pytest.mark.django_db
def test_gen_order_start_with_prefix(baseticket_factory):
    model = baseticket_factory._meta.model
    baseticket = baseticket_factory()
    baseticket.gen_order()
    assert baseticket.order.startswith(model.prefix())
