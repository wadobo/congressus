from django.template.defaultfilters import slugify
from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from events.factories import EventFactory
from windows.models import TicketWindow


class TicketWindowFactory(DjangoModelFactory):
    class Meta:
        model = TicketWindow

    event = SubFactory(EventFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
