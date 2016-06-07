from django.contrib import admin

from .models import AccessControl


class AccessControlAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'event', 'location')
    list_filter = ('event', 'location')
    search_fields = ('name', 'slug', 'event__name')


admin.site.register(AccessControl, AccessControlAdmin)
