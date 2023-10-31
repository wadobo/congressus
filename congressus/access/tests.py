import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from events.factories import (
    EventFactory,
    ExtraSessionFactory,
    SessionFactory,
    SpaceFactory,
)

from access.enums import AccessPriority
from access.factories import AccessControlFactory
from access.views import short_date
from invs.factories import InvitationFactory
from tickets.factories import MultiPurchaseFactory, TicketFactory
from tickets.models import BaseTicketMixing, Ticket


def test_access_invitation(client, user_with_group_access):
    now = timezone.now()
    tomorrow = now + timezone.timedelta(days=1)
    invitation = InvitationFactory(type__end=tomorrow, type__start=now)
    invitation.gen_order()
    event = invitation.type.event
    access = AccessControlFactory(event=event)
    session = SessionFactory(space__event=event, start=now, end=tomorrow)
    invitation.type.sessions.add(session)

    url = reverse("access", kwargs={"ev": event.slug, "ac": access.slug})
    client_session = client.session
    client_session["sessions"] = [session.id]
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
    session["sessions"] = [baseticket.session_id]
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
            {"st": "right", "extra": "Ok: E1 - S1", "extra2": ""},
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
            {"st": "maybe", "extra": "Some used: read individually", "extra2": ""},
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
    client,
    user_with_group_access,
    django_assert_max_num_queries,
    mp,
    tickets,
    order,
    expected,
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
    access = AccessControlFactory(event=event, mark_used=False)

    url = reverse("access", kwargs={"ev": event.slug, "ac": access.slug})
    session = client.session
    session["sessions"] = [session_obj.id]
    session["gate"] = gate_name
    session.save()
    client.force_login(user_with_group_access)

    with django_assert_max_num_queries(10) as num_queries:
        response = client.post(url, data={"order": order})
    print("NUM QUERIES", len(num_queries.captured_queries))
    assert response.status_code == 200
    assert json.loads(response.content) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("tickets", "has_conflict"),
    [
        ([{"session": "S1"}, {"session": "S1"}, {"session": "S3"}], True),
        ([{"session": "S2"}, {"session": "S2"}, {"session": "S4"}], True),
        ([{"session": "S1"}, {"session": "S2"}], False),
        ([{"session": "S3"}, {"session": "S3"}, {"session": "S4"}], False),
        ([{"session": "S1"}, {"session": "S1"}, {"session": "S4"}], False),
        ([{"session": "S2"}, {"session": "S2"}, {"session": "S3"}], False),
    ],
)
def test_mp_check_conflict(tickets, has_conflict):
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
    assert mp.tickets.all().has_session_conflict() is has_conflict


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mp", "tickets", "access", "expected"),
    [
        # 0: 1 MP with 2 RX not used and 2 RXe used
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {
                    "session": "RX",
                    "order": "TAAAAAAAAAAAAAA",
                    "used": False,
                },
                {
                    "session": "RX",
                    "order": "TAAAAAAAAAAAAAB",
                    "used": False,
                },
                {
                    "session": "EX",
                    "order": "TAAAAAAAAAAAAAC",
                    "extra": {
                        "used": True,
                        "used_date": timezone.localtime(timezone.now()).strftime(
                            settings.DATETIME_FORMAT
                        ),
                    },
                },
                {
                    "session": "EX",
                    "order": "TAAAAAAAAAAAAAD",
                    "extra": {
                        "used": True,
                        "used_date": timezone.localtime(timezone.now()).strftime(
                            settings.DATETIME_FORMAT
                        ),
                    },
                },
            ],
            {"order": "MAAAAAAAAAAAAAA", "gate": "", "sessions": ["RX", "RXe"]},
            {
                "st": "right",
                "extra": "Ok: R - RX",
                "extra2": "G 2",
            },
        ),
        # 1: 1 MP with 2 RX used and 2 RXe not used
        (
            {"order": "MAAAAAAAAAAAAAA"},
            [
                {
                    "session": "RX",
                    "order": "TAAAAAAAAAAAAAA",
                    "used": True,
                    "used_date": timezone.now(),
                },
                {
                    "session": "RX",
                    "order": "TAAAAAAAAAAAAAB",
                    "used": True,
                    "used_date": timezone.now(),
                },
                {
                    "session": "EX",
                    "order": "TAAAAAAAAAAAAAC",
                    "used": False,
                },
                {
                    "session": "EX",
                    "order": "TAAAAAAAAAAAAAD",
                    "used": False,
                },
            ],
            {"order": "MAAAAAAAAAAAAAA", "gate": "", "sessions": ["RX", "RXe"]},
            {
                "st": "right",
                "extra": "Ok: R - RXe",
                "extra2": "G 2",
            },
        ),
    ],
)
def test_access_multipurchase_several_session(
    client,
    user_with_group_access,
    django_assert_max_num_queries,
    mp,
    tickets,
    access,
    expected,
):
    event = EventFactory()
    spaces = {
        "R": SpaceFactory(event=event, name="R", numbered=False, seat_map=None),
        "E": SpaceFactory(event=event, name="E", numbered=True),
    }
    sessions = {
        "RX": SessionFactory(name="RX", space=spaces.get("R")),
        "RXe": SessionFactory(name="RXe", space=spaces.get("R")),
        "EX": SessionFactory(name="EX", space=spaces.get("E")),
        "EXpmr": SessionFactory(name="EXpmr", space=spaces.get("E")),
        "RS": SessionFactory(name="RS", space=spaces.get("R")),
        "RSe": SessionFactory(name="RSe", space=spaces.get("R")),
        "ESm": SessionFactory(name="ESm", space=spaces.get("E")),
        "ESmpmr": SessionFactory(name="ESm", space=spaces.get("E")),
        "ESt": SessionFactory(name="ESt", space=spaces.get("E")),
        "EStpmr": SessionFactory(name="ESt", space=spaces.get("E")),
    }

    an_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    an_hour_later = timezone.now() + timezone.timedelta(hours=1)
    ExtraSessionFactory(
        orig=sessions.get("EX"),
        extra=sessions.get("RXe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )
    ExtraSessionFactory(
        orig=sessions.get("EXpmr"),
        extra=sessions.get("RXe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )

    ExtraSessionFactory(
        orig=sessions.get("ESt"),
        extra=sessions.get("RSe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )
    ExtraSessionFactory(
        orig=sessions.get("EStpmr"),
        extra=sessions.get("RSe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )

    with patch.object(BaseTicketMixing, "send_confirm_email"):
        tickets_obj = []
        for ticket in tickets:
            session = sessions.get(ticket.pop("session"))
            gate = ticket.pop("gate", "")
            extra = ticket.pop("extra", {})
            ticket_obj = TicketFactory(
                confirmed=True, session=session, gate_name=gate, **ticket
            )
            ticket_obj.fill_duplicated_data()  # need for generate extra sessions
            extra_sessions = ticket_obj.get_extra_data("extra_sessions")
            if extra_sessions and len(extra_sessions) >= 1:
                extra_sessions[0].update(extra)
                ticket_obj.set_extra_data("extra_sessions", extra_sessions)
            ticket_obj.save()
            tickets_obj.append(ticket_obj)

    baseticket = MultiPurchaseFactory(ev=event, confirmed=True, **mp)
    baseticket.tickets.set(tickets_obj)
    access_slug = AccessControlFactory(event=event, mark_used=False).slug

    url = reverse("access", kwargs={"ev": event.slug, "ac": access_slug})
    session = client.session
    session["sessions"] = [sessions.get(_s).id for _s in access.get("sessions")]
    session["gate"] = access.get("gate")
    session.save()
    client.force_login(user_with_group_access)

    with django_assert_max_num_queries(10) as num_queries:
        response = client.post(url, data={"order": access.get("order")})
    print("NUM QUERIES", len(num_queries.captured_queries))

    assert response.status_code == 200
    assert json.loads(response.content) == expected


@pytest.mark.django_db
def test_mark_as_used():
    event = EventFactory()
    spaces = {
        "R": SpaceFactory(event=event, name="R", numbered=False, seat_map=None),
        "E": SpaceFactory(event=event, name="E", numbered=True),
    }
    sessions = {
        "RX": SessionFactory(name="RX", space=spaces.get("R")),
        "RXe": SessionFactory(name="RXe", space=spaces.get("R")),
        "EX": SessionFactory(name="EX", space=spaces.get("E")),
    }

    an_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    an_hour_later = timezone.now() + timezone.timedelta(hours=1)
    ExtraSessionFactory(
        orig=sessions.get("EX"),
        extra=sessions.get("RXe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )

    with patch.object(BaseTicketMixing, "send_confirm_email"):
        tickets_obj = []
        for session_name, order in [
            ("RX", "TAAAAAAAAAAAAAA"),
            ("RX", "TAAAAAAAAAAAAAB"),
            ("EX", "TAAAAAAAAAAAAAC"),
            ("EX", "TAAAAAAAAAAAAAD"),
        ]:
            session = sessions.get(session_name)
            ticket_obj = TicketFactory(
                confirmed=True, session=session, gate_name="", order=order
            )
            ticket_obj.fill_duplicated_data()  # need for generate extra sessions
            ticket_obj.save()
            tickets_obj.append(ticket_obj)

    mp_order = "MAAAAAAAAAAAAAA"
    mp = MultiPurchaseFactory(ev=event, confirmed=True, order=mp_order)
    mp.tickets.set(tickets_obj)

    # check tickets without using
    for ticket in mp.tickets.all():
        assert ticket.used is False
        for extra in ticket.get_extra_sessions():
            assert extra.get("used") is False

    # use session RX
    session = sessions.get("RX")
    mp.mark_as_used(session.id, AccessPriority.VALID_NORMAL)
    assert Ticket.objects.filter(session=session, used=True).count() == 2

    # use session EX
    session = sessions.get("EX")
    mp.mark_as_used(session.id, AccessPriority.VALID_NORMAL)
    assert Ticket.objects.filter(session=session, used=True).count() == 2

    # use session RXe
    session = sessions.get("RXe")
    mp.mark_as_used(session.id, AccessPriority.VALID_EXTRA)
    for ticket in mp.tickets.all():
        for extra in ticket.get_extra_sessions():
            if extra.get("session") == session.id:
                assert extra.get("used") is True


@pytest.mark.django_db
def test_mark_as_used_tickets():
    event = EventFactory()
    spaces = {
        "R": SpaceFactory(event=event, name="R", numbered=False, seat_map=None),
        "E": SpaceFactory(event=event, name="E", numbered=True),
    }
    sessions = {
        "RX": SessionFactory(name="RX", space=spaces.get("R")),
        "RXe": SessionFactory(name="RXe", space=spaces.get("R")),
        "EX": SessionFactory(name="EX", space=spaces.get("E")),
    }

    an_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    an_hour_later = timezone.now() + timezone.timedelta(hours=1)
    ExtraSessionFactory(
        orig=sessions.get("EX"),
        extra=sessions.get("RXe"),
        start=an_hour_ago,
        end=an_hour_later,
        used=False,
    )

    with patch.object(BaseTicketMixing, "send_confirm_email"):
        tickets_obj = []
        for session_name, order in [
            ("RX", "TAAAAAAAAAAAAAA"),
            ("RX", "TAAAAAAAAAAAAAB"),
            ("EX", "TAAAAAAAAAAAAAC"),
            ("EX", "TAAAAAAAAAAAAAD"),
        ]:
            session = sessions.get(session_name)
            ticket_obj = TicketFactory(
                confirmed=True, session=session, gate_name="", order=order
            )
            ticket_obj.fill_duplicated_data()  # need for generate extra sessions
            ticket_obj.save()
            tickets_obj.append(ticket_obj)

    mp_order = "MAAAAAAAAAAAAAA"
    mp = MultiPurchaseFactory(ev=event, confirmed=True, order=mp_order)
    mp.tickets.set(tickets_obj)

    # check tickets without using
    for ticket in mp.tickets.all():
        assert ticket.used is False
        for extra in ticket.get_extra_sessions():
            assert extra.get("used") is False

    # use session RX
    session = sessions.get("RX")
    for ticket in mp.tickets.filter(session=session):
        ticket.mark_as_used(session.id, AccessPriority.VALID_NORMAL)
    assert Ticket.objects.filter(session=session, used=True).count() == 2

    # use session EX
    session = sessions.get("EX")
    for ticket in mp.tickets.filter(session=session):
        ticket.mark_as_used(session.id, AccessPriority.VALID_NORMAL)
    assert Ticket.objects.filter(session=session, used=True).count() == 2

    # use session RXe
    session = sessions.get("RXe")
    for ticket in mp.tickets.filter(session__name="EX"):
        ticket.mark_as_used(session.id, AccessPriority.VALID_EXTRA)

    for ticket in mp.tickets.all():
        for extra in ticket.get_extra_sessions():
            if extra.get("session") == session.id:
                assert extra.get("used") is True


# 1 MP: 2T R1, 2T E1. if MP --> used 2 T E1 si entra en hora
#                     if MP --> used 2 T R1 si no entra en hora
#                     if MP --> used 2 T R1 si están marcados como usados los E1
#                     if MP --> invalid si todo usado
#                     if MP --> leer individual si algún T ha sido leído por separado
# Que pasa si leemos un 1T E1 individual, y luego leemos grupal, nos queda 1T E1 suelto
