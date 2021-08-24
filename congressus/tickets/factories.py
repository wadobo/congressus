from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from events.factories import SessionFactory
from tickets.models import Ticket


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    session = SubFactory(SessionFactory)
    email = Faker('email')
