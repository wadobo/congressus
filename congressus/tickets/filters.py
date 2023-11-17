from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from events.models import Session
from windows.models import TicketWindow


class TicketWindowFilter(admin.SimpleListFilter):
    title = _("Window ticket")
    parameter_name = "twin"

    def lookups(self, request, model_admin):
        ticket_windows = TicketWindow.objects.select_related("event")
        if current_event := request.session.get("current_event", None):
            ticket_windows = [tw for tw in ticket_windows if tw.event == current_event]
        ws = [(tw.id, "%s - %s" % (tw.event, tw.name)) for tw in ticket_windows]
        ws = [("--", _("without ticket window"))] + ws
        return ws

    def queryset(self, request, queryset):
        if not self.value():
            return queryset.select_related("ev")

        if self.value() != "--":
            return queryset.filter(sales__window__id=self.value()).select_related("ev")
        else:
            return queryset.filter(sales__window=None).select_related("ev")


class SingleTicketWindowFilter(TicketWindowFilter):
    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() != "--":
            return queryset.filter(mp__sales__window__id=self.value())
        else:
            return queryset.filter(mp__sales__window=None)


class SessionFilter(admin.SimpleListFilter):
    title = _("Session")
    parameter_name = "session"

    def lookups(self, request, model_admin):
        if current_event := request.session.get("current_event", None):
            sessions = Session.objects.filter(
                space__event=current_event
            ).select_related("space")
        else:
            sessions = Session.objects.select_related("space")
        return [
            (session.id, f"{session.name} {session.space.name}") for session in sessions
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        return queryset.filter(session__id=self.value())
