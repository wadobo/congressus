import json
from django.core import serializers

from websocket_server import WebsocketServer
from access.models import AccessControl
from access.models import LogAccessControl
from events.models import Event
from events.models import Session
from events.models import SeatLayout
from tickets.models import TicketSeatHold


class WSServer:
    def __init__(self, port=9007):
        self.port = port
        self.server = WebsocketServer(self.port, host='0.0.0.0')
        self.server.set_fn_new_client(self.on_connect)
        self.server.set_fn_message_received(self.on_msg)
        self.server.set_fn_client_left(self.on_disconnect)

    def on_connect(self, client, server):
        #server.send_message_to_all("Hey all, a new client has joined us")
        pass

    def on_disconnect(self, client, server):
        #server.send_message_to_all("Hey all, a new client has joined us")
        pass

    def on_msg(self, client, server, message):
        try:
            args = message.split(' ')
            command = args[0]
            args = args[1:]
            internal = 'internal_ws_' + command
            if hasattr(self, internal):
                getattr(self, internal)(client, *args)
            else:
                data = {'action': 'cmd', 'msg': 'not found'}
                self.server.send_message(client, json.dumps(data))
        except Exception as e:
            print("Error: ", e)

    def run(self):
        self.server.run_forever()

    def drop_seat(self, hold):
        row, col = hold.seat.split('-')
        data = {
            'action': 'drop',
            'session': hold.session.id,
            'layout': hold.layout.id,
            'row': row,
            'col': col,
        }

        confirmed = not hold.session.is_seat_available(hold.layout, row, col)
        if confirmed:
            data['action'] = 'confirm'

        hold.delete()
        self.server.send_message_to_all(json.dumps(data))

    # Protocol definitions

    def internal_ws_get_events(self, client):
        events = serializers.serialize("json", Event.objects.all())
        self.server.send_message(client, events)

    def internal_ws_get_spaces(self, client, event):
        event = Event.objects.get(slug=event)
        spaces = serializers.serialize("json", event.spaces.all())
        self.server.send_message(client, spaces)

    def internal_ws_get_sessions(self, client, event, space):
        event = Event.objects.get(slug=event)
        space = event.spaces.get(slug=space)
        sessions = serializers.serialize("json", space.sessions.all())
        self.server.send_message(client, sessions)

    def internal_ws_hold_seat(self, client, session, layout, row, col, user):
        session = Session.objects.get(id=session)
        layout = SeatLayout.objects.get(id=layout)
        data = {
            'action': 'hold',
            'session': session.id,
            'layout': layout.id,
            'row': row,
            'col': col,
        }

        if not session.is_seat_holded(layout, row, col):
            seat = row + '-' + col
            sh = TicketSeatHold(client=user, layout=layout, seat=seat,
                                session=session)
            sh.save()
            self.server.send_message_to_all(json.dumps(data))
        else:
            data['action'] = 'holded'
            self.server.send_message(client, json.dumps(data))

    def internal_ws_drop_seat(self, client, session, layout, row, col, user):
        session = Session.objects.get(id=session)
        layout = SeatLayout.objects.get(id=layout)
        data = {
            'action': 'drop',
            'session': session.id,
            'layout': layout.id,
            'row': row,
            'col': col,
        }

        try:
            seat = row + '-' + col
            sh = TicketSeatHold.objects.get(client=user,
                                            layout=layout,
                                            seat=seat,
                                            session=session)
            sh.delete()
            self.server.send_message_to_all(json.dumps(data))
        except:
            pass

    def internal_ws_add_ac(self, client, control, date, st):
        data = {
            'action': 'add_ac',
            'control': control,
            'date': date,
            'st': st,
        }
        log = LogAccessControl(access_control=AccessControl.objects.get(slug=control), status=st)
        log.save()
        self.server.send_message_to_all(json.dumps(data))

    def internal_ws_add_sale(self, client, window, date, payment, amount):
        data = {
            'action': 'add_sale',
            'window': window,
            'date': date,
            'payment': payment,
            'amount': amount,
        }
        self.server.send_message_to_all(json.dumps(data))
