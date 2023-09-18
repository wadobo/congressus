import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from events.factories import (
    EventFactory,
    ExtraSessionFactory,
    SessionFactory,
    SpaceFactory,
)

from access.factories import AccessControlFactory
from access.views import short_date
from invs.factories import InvitationFactory
from tickets.factories import MultiPurchaseFactory, TicketFactory
from tickets.models import BaseTicketMixing


def test_access_invitation(client, user_with_group_access):
    now = timezone.now()
    tomorrow = now + timezone.timedelta(days=1)
    # TODO: test with start and end in InvitationType
    invitation = InvitationFactory(type__end=None, type__start=None)
    invitation.gen_order()
    event = invitation.type.event
    access = AccessControlFactory(event=event)
    session = SessionFactory(space__event=event, start=now, end=tomorrow)
    invitation.type.sessions.add(session)

    url = reverse("access", kwargs={"ev": event.slug, "ac": access.slug})
    client_session = client.session
    client_session["session"] = session.id
    client_session["gate"] = ""
    client_session.save()
    client.force_login(user_with_group_access)
    response = client.post(url, data={"order": invitation.order})
    assert response.status_code == 200

    output = json.loads(response.content)
    assert output.get("st") == "right", response.content


@pytest.mark.django_db
def test_access_ticket(client, user_with_group_access):
    baseticket = TicketFactory(confirmed=True)
    baseticket.gen_order()
    event = baseticket.event()
    access = AccessControlFactory(event=event)

    url = reverse("access", kwargs={"ev": event.slug, "ac": access.slug})
    session = client.session
    session["session"] = baseticket.session_id
    session["gate"] = "A"
    session.save()
    client.force_login(user_with_group_access)
    response = client.post(url, data={"order": baseticket.order})
    assert response.status_code == 200

    output = json.loads(response.content)
    assert output.get("st") == "right", response.content


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mp", "tickets", "order", "expected"),
    [
        # 0: 1 MP with 1 T. Read MP
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [{"order": "TAAAAAAAAAAAAAA"}],
            "MAAAAAAAAAAAAAA",
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": "G 1"},
        ),
        # 1: 1 MP with 1 T. Read T
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [{"order": "TAAAAAAAAAAAAAA"}],
            "TAAAAAAAAAAAAAA",
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": ""},
        ),
        # 2: 1 MP with 1 T used. Read MP
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [{"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()}],
            "MAAAAAAAAAAAAAA",
            {
                "st": "wrong",
                "extra": f"Used: {short_date(timezone.now())}",
                "extra2": "E1 - S1",
            },
        ),
        # 3: 1 MP with 1 T used. Read T
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [{"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()}],
            "TAAAAAAAAAAAAAA",
            {
                "st": "wrong",
                "extra": f"Used: {short_date(timezone.now())}",
                "extra2": "E1 - S1",
            },
        ),
        # 4: 1 MP with 2 T. Read MP
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA"},
                {"order": "TAAAAAAAAAAAAAB"},
            ],
            "MAAAAAAAAAAAAAA",
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": "G 2"},
        ),
        # 5: 1 MP with 2 T. Read T
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA"},
                {"order": "TAAAAAAAAAAAAAB"},
            ],
            "TAAAAAAAAAAAAAA",
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": ""},
        ),
        # 6: 1 MP with 2 T used. Read MP
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()},
                {"order": "TAAAAAAAAAAAAAB", "used": True, "used_date": timezone.now()},
            ],
            "MAAAAAAAAAAAAAA",
            {
                "st": "wrong",
                "extra": f"Used: {short_date(timezone.now())}",
                "extra2": "E1 - S1",
            },
        ),
        # 7: 1 MP with 2 T used. Read T
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()},
                {"order": "TAAAAAAAAAAAAAB", "used": True, "used_date": timezone.now()},
            ],
            "TAAAAAAAAAAAAAA",
            {
                "st": "wrong",
                "extra": f"Used: {short_date(timezone.now())}",
                "extra2": "E1 - S1",
            },
        ),
        # 8: 1 MP with 2 T and 1 used. Read M
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()},
                {"order": "TAAAAAAAAAAAAAB", "used_date": timezone.now()},
            ],
            "MAAAAAAAAAAAAAA",
            {"st": "wrong", "extra": "Some used: read individually", "extra2": ""},
        ),
        # 9: 1 MP with 2 T and 1 used. Read T not used
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {"order": "TAAAAAAAAAAAAAA", "used": True, "used_date": timezone.now()},
                {"order": "TAAAAAAAAAAAAAB", "used_date": timezone.now()},
            ],
            "TAAAAAAAAAAAAAB",
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": ""},
        ),
    ],
)
def test_access_multipurchase_same_session(
    client, user_with_group_access, mp, tickets, order, expected
):
    session_obj = SessionFactory(name="S1", space__name="E1")
    gate_name = "A"
    with patch.object(BaseTicketMixing, "send_confirm_email"):
        tickets_obj = [
            TicketFactory(
                confirmed=True, session=session_obj, gate_name=gate_name, **ticket
            )
            for ticket in tickets
        ]
    baseticket = MultiPurchaseFactory(confirmed=True, tickets=tickets_obj, **mp)
    event = baseticket.event()
    access = AccessControlFactory(event=event)

    url = reverse("access", kwargs={"ev": event.slug, "ac": access.slug})
    session = client.session
    session["session"] = session_obj.id
    session["gate"] = gate_name
    session.save()
    client.force_login(user_with_group_access)

    response = client.post(url, data={"order": order})
    assert response.status_code == 200
    assert json.loads(response.content) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("tickets", "is_valid_group"),
    [
        # INVALID
        # Only one Ticket
        ([{"session": "S1"}], False),
        # More than 20 tickets
        (21 * [{"session": "S1"}], False),
        # Different sessions with extra session and conflict
        ([{"session": "S1"}, {"session": "S3"}], False),
        ([{"session": "S2"}, {"session": "S4"}], False),

        # VALID
        # All tickets same sessions, lte=20
        (3 * [{"session": "S1"}], True),
        (20 * [{"session": "S1"}], True),
        # Different sessions without extra sessions
        ([{"session": "S1"}, {"session": "S2"}], True),
        # Different sessions with extra session without conflict
        ([{"session": "S3"}, {"session": "S4"}], True),
        ([{"session": "S1"}, {"session": "S4"}], True),
        ([{"session": "S2"}, {"session": "S3"}], True),
    ],
)
def test_mp_check_valid_group(tickets, is_valid_group):
    event = EventFactory()
    spaces = {
        "SP1": SpaceFactory(event=event, name="SP1", numbered=False, seat_map=None),
        "SP2": SpaceFactory(event=event, name="SP2", numbered=True),
    }
    sessions = {
        "S1": SessionFactory(name="S1", space=spaces.get("SP1")),
        "S2": SessionFactory(name="S2", space=spaces.get("SP2")),
        "S3": SessionFactory(name="S3", space=spaces.get("SP1")),
        "S4": SessionFactory(name="S4", space=spaces.get("SP2")),
    }

    ExtraSessionFactory(orig=sessions.get("S3"), extra=sessions.get("S1")),
    ExtraSessionFactory(orig=sessions.get("S4"), extra=sessions.get("S2")),

    ticket_objs = []
    for ticket in tickets:
        ticket_obj = TicketFactory(session=sessions.get(ticket.get("session")))
        ticket_obj.gen_order()
        ticket_objs.append(ticket_obj)

    mp = MultiPurchaseFactory(ev=event)
    mp.tickets.set(ticket_objs)
    assert mp.check_valid_group() is is_valid_group
