from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from events.forms import TicketTemplateForm
from events.models import (
    ConfirmEmail,
    Discount,
    EmailAttachment,
    Event,
    ExtraSession,
    Gate,
    InvCode,
    SeatLayout,
    SeatMap,
    Session,
    Space,
    TicketField,
    TicketTemplate,
)


class GlobalEventFilter(admin.SimpleListFilter):
    title = _("Event")
    parameter_name = "event"

    def lookups(self, request, model_admin):
        return Event.read_objects.choices()

    def queryset(self, request, queryset):
        current_event = self.value() or request.session.get("current_event", None)
        if current_event:
            return queryset.filter(**{self.parameter_name: current_event})
        return queryset


class GlobalSpaceEventFilter(GlobalEventFilter):
    parameter_name = "space__event"


class InvCodeInline(admin.TabularInline):
    model = InvCode


@admin.register(InvCode)
class InvCodeAdmin(admin.ModelAdmin):
    list_display = ("event", "person", "code", "type", "used")
    list_filter = (GlobalEventFilter, "used", "type")
    search_fields = ("event", "person", "code")


class SpaceInline(admin.TabularInline):
    model = Space


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("event", "order", "name", "capacity", "numbered")
    list_filter = (GlobalEventFilter, "capacity", "numbered")
    search_fields = ("event__name", "name")
    prepopulated_fields = {"slug": ["name"]}


class TicketFieldInline(admin.TabularInline):
    model = TicketField


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [SpaceInline, TicketFieldInline, InvCodeInline]
    list_display = ("name", "active", "ticket_sale_enabled", "sold")
    list_filter = ("active",)
    filter_horizontal = ("discounts",)
    prepopulated_fields = {"slug": ["name"]}

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .with_amount_sold_tickets()
        )

    def sold(self, obj):
        return obj.amount_sold_tickets


class Attachments(admin.TabularInline):
    model = EmailAttachment


@admin.register(ConfirmEmail)
class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ("event", "subject")
    list_filter = (GlobalEventFilter,)
    search_fields = ("event", "subject", "body")


class ExtraSessionInline(admin.TabularInline):
    model = ExtraSession
    fk_name = "orig"


class GlobalOrigSpaceEventFilter(GlobalEventFilter):
    parameter_name = "orig__space__event"


@admin.register(ExtraSession)
class ExtraSessionAdmin(admin.ModelAdmin):
    list_display = ("orig", "extra", "start", "end", "used")
    list_filter = (GlobalOrigSpaceEventFilter,)


class CustomSpaceFilter(admin.SimpleListFilter):
    title = _("space")
    parameter_name = "space"

    def lookups(self, request, model_admin):
        spaces = Space.objects.select_related("event")
        if current_event := request.session.get("current_event", None):
            spaces = spaces.filter(event=current_event)
        return [(str(sp.id), str(sp)) for sp in spaces]

    def queryset(self, request, queryset):
        qs = queryset.select_related("space", "space__event")
        if not self.value():
            return qs

        return qs.filter(space=self.value())


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    inlines = [ExtraSessionInline]
    list_display = ("space", "name", "start", "end", "price", "tax")
    list_filter = (GlobalSpaceEventFilter, CustomSpaceFilter)
    search_fields = ("space__name", "name", "space__event__name")
    prepopulated_fields = {"slug": ["name"]}

    date_hierarchy = "start"


@admin.register(SeatMap)
class SeatMapAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(SeatLayout)
class SeatLayoutAdmin(admin.ModelAdmin):
    list_display = ("name", "map", "top", "left", "direction")
    list_filter = ("map",)
    search_fields = ("map__name", "name")


@admin.register(Gate)
class GateAdmin(admin.ModelAdmin):
    list_display = ("event", "name")
    list_filter = (GlobalEventFilter,)


@admin.register(TicketTemplate)
class TicketTemplateAdmin(admin.ModelAdmin):
    form = TicketTemplateForm
    list_display = ("name",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "value")
