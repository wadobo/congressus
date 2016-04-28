from django.contrib import admin

from .models import Event, InvCode
from .models import ConfirmEmail, EmailAttachment
from .models import Space


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
    search_fields = ('event', 'name')


class EventAdmin(admin.ModelAdmin):
    inlines = [SpaceInline, InvCodeInline]
    list_display = ('name', 'start', 'end', 'active', 'price', 'max', 'sold')
    list_filter = ('active',)
    date_hierarchy = 'start'

    def sold(self, obj):
        return obj.sold()


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = ('event',)
    search_fields = ('event', 'subject', 'body')


admin.site.register(Event, EventAdmin)
admin.site.register(InvCode, InvCodeAdmin)
admin.site.register(Space, SpaceAdmin)
admin.site.register(ConfirmEmail, ConfirmEmailAdmin)
