import pytest
from django.db import connection, reset_queries

from events.factories import (
    ExtraSessionFactory,
    EventFactory,
    SeatLayoutFactory,
    SessionFactory,
)
from invs.models import Invitation, InvitationGenerator
from invs.factories import InvitationTypeFactory


@pytest.mark.django_db
@pytest.mark.parametrize(('invitation_number', 'seat_layouts', 'col'), [
    (100, 2, 10),
    (200, 5, 10),
    (1000, 10, 50),
    #(8000, 10, 50),
])
def test_payment(invitation_number, seat_layouts, col):
    event = EventFactory()
    session = SessionFactory()
    ExtraSessionFactory.create_batch(3, orig=session)
    invitation_type = InvitationTypeFactory(event=event)
    invitation_type.sessions.add(session)

    seats = ''
    for idx in range(seat_layouts):
        SeatLayoutFactory(map=session.space.seat_map, name=f'C{idx + 1}')
        row = int(invitation_number / col / seat_layouts)
        seats += f'C1[1-1:{col}-{row}];'

    generator = InvitationGenerator(
        type=invitation_type,
        amount=invitation_number,
        price=100,
        tax=21,
        concept='test',
        seats=seats[:-1]
    )
    reset_queries()
    generator.save()
    db_queries = len(connection.queries)

    assert Invitation.objects.count() == invitation_number
    assert db_queries < invitation_number * 4
