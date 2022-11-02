from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from django.template.defaultfilters import slugify

from access.models import AC_TYPES, AccessControl, LogAccessControl
from events.factories import EventFactory


class AccessControlFactory(DjangoModelFactory):
    class Meta:
        model = AccessControl

    event = SubFactory(EventFactory)
    name = Faker('name')
    slug = LazyAttribute(lambda obj: slugify(obj.name))
    location = Faker('name')
    mark_used = Faker('pybool')


class LogAccessControlFactory(DjangoModelFactory):
    class Meta:
        model = LogAccessControl

    access_control = SubFactory(AccessControlFactory)
    date = Faker('date_time')
    status = Faker('random_element', elements=[ac_type[0] for ac_type in AC_TYPES])
