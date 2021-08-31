from django.template.defaultfilters import slugify
from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from events.models import Discount, Event, Session, Space, TicketTemplate


class TicketTemplateFactory(DjangoModelFactory):
    class Meta:
        model = TicketTemplate

    name = Faker('name')
    note = Faker('sentence')
    links = Faker('url')
    info = Faker('sentence')
    pagesize_width = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)
    pagesize_height = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)
    left_margin = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)
    right_margin = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)
    bottom_margin = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)
    top_margin = Faker('pyfloat', left_digits=1, right_digits=2, positive=True)


class DiscountFactory(DjangoModelFactory):
    class Meta:
        model = Discount

    name = Faker('name')
    #type = Faker('random_element', elements=Discount.DISCOUNT_TYPES)


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
    info = Faker('sentence')


class SpaceFactory(DjangoModelFactory):
    class Meta:
        model = Space

    event = SubFactory(EventFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))


class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    space = SubFactory(SpaceFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
    start = Faker('date_time')
    end = Faker('date_time')

    template = SubFactory(TicketTemplateFactory)
