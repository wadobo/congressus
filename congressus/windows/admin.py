from django.contrib import admin

from .models import TicketWindow


class TicketWindowAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'event', 'location')
    list_filter = ('event', 'location')
    search_fields = ('name', 'slug', 'event__name')
    filter_horizontal = ('users', )


admin.site.register(TicketWindow, TicketWindowAdmin)
