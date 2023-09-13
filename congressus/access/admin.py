from django.contrib import admin

from .models import AccessControl
from .models import LogAccessControl

from events.admin import GlobalEventFilter


@admin.register(AccessControl)
class AccessControlAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'event', 'location', 'mark_used')
    list_filter = (GlobalEventFilter, 'location')
    search_fields = ('name', 'slug', 'event__name')


@admin.register(LogAccessControl)
class LogAccessControlAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    list_display = ('access_control', 'status', 'date')
    list_filter = ('status',)

    date_hierarchy = 'date'
