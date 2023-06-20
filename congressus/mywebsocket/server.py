import json
import datetime
from django.core import serializers
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import connection

from threading import Lock
from threading import Timer

from websocket_server import WebsocketServer
from access.models import AccessControl
from access.models import LogAccessControl
from events.models import Event
from events.models import Session
from events.models import SeatLayout
from tickets.models import TicketSeatHold
from tickets.utils import search_seats


class WSServer:
    def __init__(self, port=9007):
        self.port = port
        self.server = WebsocketServer(self.port, host="0.0.0.0")
        self.server.set_fn_new_client(self.on_connect)
        self.server.set_fn_message_received(self.on_msg)
        self.server.set_fn_client_left(self.on_disconnect)
        self.msg_lock = Lock()

    def ping(self):
        self.server.send_message_to_all(json.dumps({"action": "ping"}))

        # pinging every 50 seconds to avoid disconnection
        t = Timer(50, self.ping)
        t.start()

    def on_connect(self, client, server):
        # server.send_message_to_all("Hey all, a new client has joined us")
        pass

    def on_disconnect(self, client, server):
        # server.send_message_to_all("Hey all, a new client has joined us")
        pass

    def on_msg(self, client, server, message):
        self.msg_lock.acquire()
        try:
            args = message.split(" ")
            command = args[0]
            args = args[1:]
            internal = "internal_ws_" + command
            if hasattr(self, internal):
                getattr(self, internal)(client, *args)
            else:
                data = {"action": "cmd", "msg": "not found"}
                self.server.send_message(client, json.dumps(data))
        except Exception as e:
            print("Error: ", e)

        connection.close()
        self.msg_lock.release()

    def run(self):
        self.ping()
        self.server.run_forever()

    def drop_seat(self, hold):
        session = hold.session
        layout = hold.layout

        row, col = hold.seat.split("-")
        data = {
            "action": "drop",
            "session": session.id,
            "layout": layout.id,
            "row": row,
            "col": col,
        }

        hold.delete()

        confirmed = not session.is_seat_available(layout, row, col)
        if confirmed:
            data["action"] = "confirm"

        self.server.send_message_to_all(json.dumps(data))

    def notify_confirmed(self):
        d = timezone.now()
        d = d - datetime.timedelta(seconds=80)
        holds = TicketSeatHold.objects.filter(date__gt=d, type="R")
        for h in holds:
            row, col = h.seat.split("-")
            data = {
                "action": "confirm",
                "session": h.session.id,
                "layout": h.layout.id,
                "row": row,
                "col": col,
            }
            self.server.send_message_to_all(json.dumps(data))

    # Protocol definitions

    def internal_ws_autoseats(self, client, session, amount, user):
        session = Session.objects.get(id=session)
        seats = search_seats(session, int(amount))
        data = {
            "action": "autoseat",
            "session": session.id,
            "seats": seats,
        }

        for s in seats:
            layout = SeatLayout.objects.get(id=s["layout"])
            seat = "{}-{}".format(s["row"], s["col"])

            d2 = {
                "action": "hold",
                "session": session.id,
                "layout": layout.id,
                "row": s["row"],
                "col": s["col"],
            }
            sh = TicketSeatHold(client=user, layout=layout, seat=seat, session=session)
            sh.save()
            self.server.send_message_to_all(json.dumps(d2))

        if not seats:
            data["error"] = _(
                "Not found contiguous seats, please, select manually using the green button"
            )

        self.server.send_message(client, json.dumps(data))

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
            "action": "hold",
            "session": session.id,
            "layout": layout.id,
            "row": row,
            "col": col,
        }

        if not session.is_seat_holded(layout, row, col):
            seat = row + "-" + col
            sh = TicketSeatHold(client=user, layout=layout, seat=seat, session=session)
            sh.save()
            self.server.send_message_to_all(json.dumps(data))
        else:
            data["action"] = "holded"
            self.server.send_message(client, json.dumps(data))

    def internal_ws_drop_seat(self, client, session, layout, row, col, user):
        try:
            seat = row + "-" + col
            sh = TicketSeatHold.objects.get(
                client=user, type="H", layout=layout, seat=seat, session=session
            )
            self.drop_seat(sh)
        except Exception:
            pass

    def internal_ws_add_ac(self, client, control, date, st):
        data = {
            "action": "add_ac",
            "control": control,
            "date": date,
            "st": st,
        }
        log = LogAccessControl(
            access_control=AccessControl.objects.get(slug=control), status=st
        )
        log.save()
        self.server.send_message_to_all(json.dumps(data))

    def internal_ws_add_sale(self, client, window, date, payment, amount, price):
        data = {
            "action": "add_sale",
            "window": window,
            "date": date,
            "payment": payment,
            "amount": amount,
            "price": price,
        }
        self.server.send_message_to_all(json.dumps(data))

    def internal_ws_add_change(self, client, window, date, payment, amount, price):
        data = {
            "action": "add_change",
            "window": window,
            "date": date,
            "payment": payment,
            "amount": amount,
            "price": price,
        }
        self.server.send_message_to_all(json.dumps(data))
