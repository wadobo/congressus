from django.conf import settings
from django.template.defaultfilters import slugify
from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from events.models import (
    DIRECTIONS,
    Discount,
    Gate,
    Event,
    ExtraSession,
    SeatLayout,
    SeatMap,
    Session,
    Space,
    TicketTemplate,
)


class TicketTemplateFactory(DjangoModelFactory):
    class Meta:
        model = TicketTemplate

    name = Faker('name')
    note = Faker('sentence')
    links = Faker('url')
    info = Faker('sentence')
    pagesize_width = Faker('pyfloat', left_digits=3, right_digits=2, positive=True)
    pagesize_height = Faker('pyfloat', left_digits=3, right_digits=2, positive=True)
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


class SeatMapFactory(DjangoModelFactory):
    class Meta:
        model = SeatMap

    name = Faker('name')
    scene_top = Faker('pyint', min_value=0, max_value=10)
    scene_bottom = Faker('pyint', min_value=0, max_value=10)
    scene_left = Faker('pyint', min_value=0, max_value=10)
    scene_right = Faker('pyint', min_value=0, max_value=10)


class SpaceFactory(DjangoModelFactory):
    class Meta:
        model = Space

    event = SubFactory(EventFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
    seat_map = SubFactory(SeatMapFactory)


class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    space = SubFactory(SpaceFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
    start = Faker('date_time', tzinfo=settings.TZINFO)
    end = Faker('date_time', tzinfo=settings.TZINFO)

    template = SubFactory(TicketTemplateFactory)
    window_template = SubFactory(TicketTemplateFactory)


class ExtraSessionFactory(DjangoModelFactory):
    class Meta:
        model = ExtraSession

    orig = SubFactory(SessionFactory)
    extra = SubFactory(SessionFactory)
    start = Faker('date_time', tzinfo=settings.TZINFO)
    end = Faker('date_time', tzinfo=settings.TZINFO)
    used = Faker('pybool')


class GateFactory(DjangoModelFactory):
    class Meta:
        model = Gate

    event = SubFactory(EventFactory)
    name = Faker('name')


class SeatLayoutFactory(DjangoModelFactory):
    class Meta:
        model = SeatLayout

    map = SubFactory(SeatMapFactory)
    name = Faker('name')
    top = Faker('pyint', min_value=0, max_value=10)
    left = Faker('pyint', min_value=0, max_value=10)
    direction = Faker('random_element', elements=[direction[0] for direction in DIRECTIONS])
    layout = ''  # L_R
    column_start_number = Faker('pyint', min_value=0, max_value=10)
    gate = SubFactory(GateFactory)
