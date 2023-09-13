from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from events.factories import EventFactory, SessionFactory
from tickets.models import MultiPurchase, Ticket


class MultiPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = MultiPurchase

    ev = SubFactory(EventFactory)

    order = Faker('pystr', max_chars=20)
    order_tpv = Faker('pystr', max_chars=12)


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    mp = SubFactory(MultiPurchaseFactory)
    session = SubFactory(SessionFactory)
    email = Faker('email')
    order_tpv = Faker('pystr', min_chars=12, max_chars=12)
