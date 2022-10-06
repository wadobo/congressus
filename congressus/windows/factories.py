from django.template.defaultfilters import slugify
from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from events.factories import EventFactory
from tickets.factories import MultiPurchaseFactory
from windows.models import TicketWindow, TicketWindowSale


class TicketWindowFactory(DjangoModelFactory):
    class Meta:
        model = TicketWindow

    event = SubFactory(EventFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))


class TicketWindowSaleFactory(DjangoModelFactory):
    class Meta:
        model = TicketWindowSale

    window = SubFactory(TicketWindowFactory)
    purchase = SubFactory(MultiPurchaseFactory)
