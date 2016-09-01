from django.contrib import admin

from .models import AccessControl
from .models import LogAccessControl



class AccessControlAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'event', 'location', 'mark_used')
    list_filter = ('event', 'location')
    search_fields = ('name', 'slug', 'event__name')


class LogAccessControlAdmin(admin.ModelAdmin):
    list_display = ('access_control', 'status')
    readonly_fields = ('date',)
    list_display = ('access_control', 'status', 'date')


admin.site.register(AccessControl, AccessControlAdmin)
admin.site.register(LogAccessControl, LogAccessControlAdmin)
