from django.contrib import admin

from .models import Event, InvCode
from .models import ExtraSession
from .models import ConfirmEmail, EmailAttachment
from .models import Space
from .models import Session
from .models import TicketField
from .models import SeatMap, SeatLayout, Gate
from .models import TicketTemplate
from .models import ThermalTicketTemplate
from .models import Discount

from congressus.admin import register


EVFilter = ('event', admin.RelatedOnlyFieldListFilter)


class EventMixin:
    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(event__slug=slug)


class SpaceMixin:
    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(space__event__slug=slug)


class InvCodeInline(admin.TabularInline):
    model = InvCode


class InvCodeAdmin(EventMixin, admin.ModelAdmin):
    list_display = ('event', 'person', 'code', 'type', 'used')
    list_filter = (EVFilter, 'used', 'type')
    search_fields = ('event', 'person', 'code')


class SpaceInline(admin.TabularInline):
    model = Space


class SpaceAdmin(EventMixin, admin.ModelAdmin):
    list_display = ('event', 'order', 'name', 'capacity', 'numbered')
    list_filter = (EVFilter, 'capacity', 'numbered')
    search_fields = ('event__name', 'name')


class TicketFieldInline(admin.TabularInline):
    model = TicketField


class EventAdmin(admin.ModelAdmin):
    inlines = [SpaceInline, TicketFieldInline, InvCodeInline]
    list_display = ('name', 'active', 'ticket_sale_enabled', 'sold')
    list_filter = ('active',)
    filter_horizontal = ('discounts',)

    def sold(self, obj):
        return obj.sold()


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(EventMixin, admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = (EVFilter,)
    search_fields = ('event', 'subject', 'body')


class ExtraSessionInline(admin.TabularInline):
    model = ExtraSession
    fk_name = 'orig'


class ExtraSessionAdmin(admin.ModelAdmin):
    list_display = ('orig', 'extra', 'start', 'end', 'used')

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(orig__space__event__slug=slug)


class SessionAdmin(SpaceMixin, admin.ModelAdmin):
    inlines = [ExtraSessionInline]
    list_display = ('space', 'name', 'start', 'end', 'price', 'tax')
    list_filter = (('space', admin.RelatedOnlyFieldListFilter), )
    search_fields = ('space__name', 'name', 'space__event__name')

    date_hierarchy = 'start'


class SeatMapAdmin(admin.ModelAdmin):
    list_display = ('name', )
    list_filter = ('name', )
    search_fields = ('name', )


class SeatLayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'map', 'top', 'left', 'direction')
    list_filter = ('map', )
    search_fields = ('map__name', 'name')


class GateAdmin(EventMixin, admin.ModelAdmin):
    list_display = ('event', 'name')
    list_filter = (EVFilter, )


class TicketTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', )


class ThermalTicketTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', )


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'value')


register(Event, EventAdmin)
register(InvCode, InvCodeAdmin)
register(ConfirmEmail, ConfirmEmailAdmin)
register(Space, SpaceAdmin)
register(ExtraSession, ExtraSessionAdmin)
register(Session, SessionAdmin)

register(SeatMap, SeatMapAdmin)
register(SeatLayout, SeatLayoutAdmin)
register(Gate, GateAdmin)

register(TicketTemplate, TicketTemplateAdmin)
register(ThermalTicketTemplate, ThermalTicketTemplateAdmin)
register(Discount, DiscountAdmin)
