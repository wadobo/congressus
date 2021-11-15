from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from access.factories import AccessControlFactory, LogAccessControlFactory
from events.factories import EventFactory, SessionFactory


@pytest.mark.django_db
def test_access_report_one_day():
    event = EventFactory()
    session = SessionFactory(start=datetime.now(), space__event=event)
    access_control = AccessControlFactory(event=event, mark_used=True)

    log_valids = [
        LogAccessControlFactory(access_control=access_control, status='ok'),
        LogAccessControlFactory(access_control=access_control, status='right'),
    ]

    LogAccessControlFactory(access_control=access_control, status='')
    LogAccessControlFactory(access_control=access_control, status='invalid')
    LogAccessControlFactory(access_control=access_control, status='incorrect')
    LogAccessControlFactory(access_control=access_control, status='used')

    client = Client()
    url = reverse('access_report', args=[event.slug])
    response = client.get(url)
    assert response.status_code == 200

    assert response.context.get('table') == [
            ['Puntos de control', f'Accesos día {session.start.day}'],
            ['TOTALES', len(log_valids)],
            [access_control.name, len(log_valids)],
    ]
    assert response.context.get('days') == [session.start.date()]


@pytest.mark.django_db
def test_access_report_several_day():
    event = EventFactory()
    sessions = [
        SessionFactory(start=datetime.now(), space__event=event),
        SessionFactory(start=datetime.now() + timedelta(days=1), space__event=event),
        SessionFactory(start=datetime.now() + timedelta(days=2), space__event=event),
    ]

    access_controls = AccessControlFactory.create_batch(3, event=event, mark_used=True)

    valid_logs = 2
    for session in sessions:
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = session.start
            for access_control in access_controls:
                LogAccessControlFactory.create_batch(
                    valid_logs,
                    access_control=access_control,
                    status='right',
                )

    client = Client()
    url = reverse('access_report', args=[event.slug])
    response = client.get(url)
    assert response.status_code == 200

    expected_table = [
            ['Puntos de control'] + [f'Accesos día {session.start.day}' for session in sessions],
            ['TOTALES'] + [valid_logs * len(access_controls) for session in sessions],
        ] + [[ac.name] + [valid_logs] * len(sessions) for ac in access_controls]

    assert response.context.get('table') == expected_table
    assert response.context.get('days') == [session.start.date() for session in sessions]
