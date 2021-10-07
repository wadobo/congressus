from django.conf import settings
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from events.factories import EventFactory, TicketTemplateFactory

from invs.models import InvitationType


class InvitationTypeFactory(DjangoModelFactory):
    class Meta:
        model = InvitationType

    name = Faker('name')
    is_pass = Faker('pybool')
    one_time_for_session = Faker('pybool')
    event = SubFactory(EventFactory)
    #sessions = []
    #gates = []
    start = Faker('date_time', tzinfo=settings.TZINFO)
    end = Faker('date_time', tzinfo=settings.TZINFO)
    template = SubFactory(TicketTemplateFactory)
