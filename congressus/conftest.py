import pytest

from django.contrib.auth.models import Group


@pytest.fixture
def group_access(db):
    group_access, _ = Group.objects.get_or_create(name="access")
    return group_access


@pytest.fixture
def user_with_group_access(db, django_user_model, group_access):
    user = django_user_model.objects.create_user(username="test", password="****")
    user.groups.add(group_access)
    return user
