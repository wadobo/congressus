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


class InvCodeInline(admin.TabularInline):
    model = InvCode


class InvCodeAdmin(admin.ModelAdmin):
    list_display = ('event', 'person', 'code', 'type', 'used')
    list_filter = ('event', 'used', 'type')
    search_fields = ('event', 'person', 'code')


class SpaceInline(admin.TabularInline):
    model = Space


class SpaceAdmin(admin.ModelAdmin):
    list_display = ('event', 'order', 'name', 'capacity', 'numbered')
    list_filter = ('event', 'capacity', 'numbered')
    search_fields = ('event__name', 'name')


class TicketFieldInline(admin.TabularInline):
    model = TicketField


class EventAdmin(admin.ModelAdmin):
    inlines = [SpaceInline, TicketFieldInline, InvCodeInline]
    list_display = ('name', 'active', 'sold')
    list_filter = ('active',)
    filter_horizontal = ('discounts',)

    def sold(self, obj):
        return obj.sold()


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = ('event',)
    search_fields = ('event', 'subject', 'body')


class ExtraSessionInline(admin.TabularInline):
    model = ExtraSession
    fk_name = 'orig'


class ExtraSessionAdmin(admin.ModelAdmin):
    list_display = ('orig', 'extra', 'start', 'end', 'used')


class SessionAdmin(admin.ModelAdmin):
    inlines = [ExtraSessionInline]
    list_display = ('space', 'name', 'start', 'end', 'price', 'tax')
    list_filter = ('space', )
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


class GateAdmin(admin.ModelAdmin):
    list_display = ('event', 'name')
    list_filter = ('event', )


class TicketTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', )


class ThermalTicketTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', )


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'value')


admin.site.register(Event, EventAdmin)
admin.site.register(InvCode, InvCodeAdmin)
admin.site.register(ConfirmEmail, ConfirmEmailAdmin)
admin.site.register(Space, SpaceAdmin)
admin.site.register(ExtraSession, ExtraSessionAdmin)
admin.site.register(Session, SessionAdmin)

admin.site.register(SeatMap, SeatMapAdmin)
admin.site.register(SeatLayout, SeatLayoutAdmin)
admin.site.register(Gate, GateAdmin)

admin.site.register(TicketTemplate, TicketTemplateAdmin)
admin.site.register(ThermalTicketTemplate, ThermalTicketTemplateAdmin)
admin.site.register(Discount, DiscountAdmin)
