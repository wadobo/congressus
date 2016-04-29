from django.contrib import admin

from .models import Ticket
from admin_csv import CSVMixin


class TicketAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event', 'confirmed', 'email')
    list_filter = ('confirmed',)
    search_fields = ('order', 'order_tpv', 'email')
    date_hierarchy = 'created'
    csv_fields = [
        'email',

        'invcode',
        'order',
        'order_tpv',

        'confirmed_date',
        'confirm_sent',

        'eventname',
        'spacename',
        'sessionname',
        'created',
    ]

    def eventname(self, obj):
        return obj.event().name

    def spacename(self, obj):
        return obj.space().name

    def sessionname(self, obj):
        return obj.session.name

    def invcode(self, obj):
        return obj.inv.code if obj.inv else ''


admin.site.register(Ticket, TicketAdmin)
