from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory

from events.factories import EventFactory, SessionFactory, SeatLayoutFactory
from tickets.models import MultiPurchase, Ticket


class MultiPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = MultiPurchase

    ev = SubFactory(EventFactory)

    order = Faker('pystr', max_chars=20)
    order_tpv = Faker('pystr', max_chars=12)

    @post_generation
    def tickets(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of groups were passed in, use them
            for ticket in extracted:
                self.tickets.add(ticket)


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    mp = SubFactory(MultiPurchaseFactory)
    session = SubFactory(SessionFactory)
    email = Faker('email')
    order_tpv = Faker('pystr', min_chars=12, max_chars=12)
    seat_layout = SubFactory(SeatLayoutFactory)
