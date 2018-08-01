from django.contrib import admin

from .models import AccessControl
from .models import LogAccessControl

from congressus.admin import register
from events.admin import EventMixin, EVFilter


class AccessControlAdmin(EventMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'event', 'location', 'mark_used')
    list_filter = (EVFilter, 'location')
    search_fields = ('name', 'slug', 'event__name')


class LogAccessControlAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    list_display = ('access_control', 'status', 'date')
    list_filter = ('status',)

    date_hierarchy = 'date'

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(access_control__event__slug=slug)


register(AccessControl, AccessControlAdmin)
register(LogAccessControl, LogAccessControlAdmin)