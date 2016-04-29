from django.contrib import admin

from .models import Event, InvCode
from .models import ConfirmEmail, EmailAttachment
from .models import Space
from .models import Session
from .models import TicketField


class InvCodeInline(admin.TabularInline):
    model = InvCode


class InvCodeAdmin(admin.ModelAdmin):
    list_display = ('event', 'person', 'code', 'type', 'used')
    list_filter = ('event', 'used', 'type')
    search_fields = ('event', 'person', 'code')


class SpaceInline(admin.TabularInline):
    model = Space


class SpaceAdmin(admin.ModelAdmin):
    list_display = ('event', 'name', 'capacity', 'numbered')
    list_filter = ('event', 'capacity', 'numbered')
    search_fields = ('event__name', 'name')


class TicketFieldInline(admin.TabularInline):
    model = TicketField


class EventAdmin(admin.ModelAdmin):
    inlines = [SpaceInline, TicketFieldInline, InvCodeInline]
    list_display = ('name', 'active', 'sold')
    list_filter = ('active',)

    def sold(self, obj):
        return obj.sold()


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = ('event',)
    search_fields = ('event', 'subject', 'body')


class SessionAdmin(admin.ModelAdmin):
    list_display = ('space', 'name', 'start', 'end', 'price')
    list_filter = ('space', )
    search_fields = ('space__name', 'name', 'space__event__name')

    date_hierarchy = 'start'


admin.site.register(Event, EventAdmin)
admin.site.register(InvCode, InvCodeAdmin)
admin.site.register(ConfirmEmail, ConfirmEmailAdmin)
admin.site.register(Space, SpaceAdmin)
admin.site.register(Session, SessionAdmin)
