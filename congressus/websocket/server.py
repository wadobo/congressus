from django.core import serializers

from websocket_server import WebsocketServer
from events.models import Event


class WSServer:
    def __init__(self, port=9007):
        self.port = port
        self.server = WebsocketServer(self.port)
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
                self.server.send_message(client, 'Command not found')
        except Exception as e:
            print("Error: ", e)

    def run(self):
        self.server.run_forever()

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
