from django.conf import settings
from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory
from events.factories import EventFactory, TicketTemplateFactory

from invs.models import (
    InvitationType,
    InvitationGenerator,
    Invitation,
)


class InvitationTypeFactory(DjangoModelFactory):
    class Meta:
        model = InvitationType

    name = Faker("name")
    is_pass = Faker("pybool")
    one_time_for_session = Faker("pybool")
    event = SubFactory(EventFactory)
    # sessions = []
    # gates = []
    start = Faker("date_time", tzinfo=settings.TZINFO)
    end = Faker("date_time", tzinfo=settings.TZINFO)
    template = SubFactory(TicketTemplateFactory)


class InvitationGeneratorFactory(DjangoModelFactory):
    class Meta:
        model = InvitationGenerator

    type = SubFactory(InvitationTypeFactory)


class InvitationFactory(DjangoModelFactory):
    class Meta:
        model = Invitation

    type = SubFactory(InvitationTypeFactory)
    generator = SubFactory(InvitationGeneratorFactory)

    @post_generation
    def sessions(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of groups were passed in, use them
            for session in extracted:
                self.sessions.add(session)
