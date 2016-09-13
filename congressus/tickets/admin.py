from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Ticket
from .models import MultiPurchase
from .models import TicketWarning
from .models import TicketSeatHold
from admin_csv import CSVMixin


def confirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirm()
confirm.short_description = _("Manual confirm")


def unconfirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirmed = False
        i.remove_hold_seats()
        i.save()
unconfirm.short_description = _("Manual unconfirm")


class TicketAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event_name', 'confirmed', 'used', 'email', 'session', 'price', 'cseat', 'mp', 'twin')
    list_filter = ('confirmed', 'event_name')
    search_fields = ('order', 'order_tpv', 'email', 'mp__order', 'mp__order_tpv')
    date_hierarchy = 'created'
    actions = [confirm, unconfirm]
    csv_fields = [
        'email',

        'order',
        'order_tpv',

        'confirmed',
        'confirmed_date',

        'price',
        'cseat',
        'mp',
        'twin',

        'event_name',
        'space_name',
        'session_name',
        'created',
    ]

    def price(self, obj):
        return obj.get_price()

    def twin(self, obj):
        from windows.models import TicketWindowSale
        try:
            tws = TicketWindowSale.objects.get(purchase__tickets=obj)
        except:
            return '-'
        prefix = tws.window.code
        return prefix
    twin.short_description = _('ticket window')


class MPAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'ev', 'confirmed', 'email', 'price', 'ntickets', 'twin')
    list_filter = ('confirmed', 'ev')
    search_fields = ('order', 'order_tpv', 'email')
    date_hierarchy = 'created'
    actions = [confirm, unconfirm]
    csv_fields = [
        'email',

        'order',
        'order_tpv',

        'confirmed',
        'confirmed_date',

        'price',
        'ntickets',
        'twin',

        'ev',
        'created',
    ]

    def ntickets(self, obj):
        return obj.tickets.count()
    ntickets.short_description = _('ntickets')

    def twin(self, obj):
        from windows.models import TicketWindowSale
        try:
            tws = TicketWindowSale.objects.get(purchase=obj)
        except:
            return '-'
        prefix = tws.window.code
        return prefix
    twin.short_description = _('ticket window')

    def price(self, obj):
        return obj.get_price()
    price.short_description = _('price')


class TicketWarningAdmin(admin.ModelAdmin):
    list_display = ('name', 'ev',  'csessions1', 'csessions2', 'message')
    list_filter = ('name',)
    filter_horizontal = ('sessions1', 'sessions2')

    def csessions1(self, obj):
        return ', '.join(str(s) for s in obj.sessions1.all())

    def csessions2(self, obj):
        return ', '.join(str(s) for s in obj.sessions2.all())


class TicketSeatHoldAdmin(admin.ModelAdmin):
    search_fields = ('client', )
    date_hierarchy = 'date'
    list_display = ('client', 'session',  'layout', 'seat', 'date', 'type')
    list_filter = ('session', 'type', 'layout')


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketWarning, TicketWarningAdmin)
admin.site.register(MultiPurchase, MPAdmin)
admin.site.register(TicketSeatHold, TicketSeatHoldAdmin)
