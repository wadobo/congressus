from django.contrib import admin

from .models import Event, Ticket


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'active', 'price')
    list_filter = ('active',)
    date_hierarchy = 'start'


class TicketAdmin(admin.ModelAdmin):
    list_display = ('order', 'event', 'confirmed', 'name', 'surname',
                    'email')
    list_filter = ('confirmed',)
    date_hierarchy = 'created'


admin.site.register(Event, EventAdmin)
admin.site.register(Ticket, TicketAdmin)
