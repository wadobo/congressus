from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from .models import Ticket
from .models import MultiPurchase
from .models import TicketWarning
from .models import TicketSeatHold
from admin_csv import CSVMixin

from .filters import TicketWindowFilter
from windows.models import TicketWindowSale


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
        try:
            tws = TicketWindowSale.objects.get(purchase__tickets=obj)
        except:
            return '-'
        prefix = tws.window.code
        return prefix
    twin.short_description = _('ticket window')


class TicketInline(admin.TabularInline):
    model = Ticket
    fields = ('link_order', 'session', 'price', 'seat_layout', 'seat')
    readonly_fields = fields

    def link_order(self, obj):
        url = reverse('admin:tickets_ticket_change', args=(obj.id,))
        html = '<a href="' + url + '">' + obj.order + '</a>'
        return mark_safe(html)
    link_order.short_description = _('order')

    def has_delete_permission(self, request, obj):
        return False

    def has_add_permission(self, request):
        return False


class MPAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order_tpv', 'twin', 'created', 'confirmed', 'email', 'ntickets', 'price', 'event')
    list_filter = ('confirmed', TicketWindowFilter, 'ev')
    search_fields = ('order', 'order_tpv', 'email', 'extra_data')
    date_hierarchy = 'created'
    actions = [confirm, unconfirm]
    inlines = [TicketInline, ]
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

    readonly_fields = (
        'order_tpv', 'order', 'ev',
        'confirmed', 'confirmed_date',
        'ntickets', 'price', 'payment',
        'formated_extra_data',
    )

    fieldsets = (
        (None, {
            'fields': ('order_tpv', 'order', 'ev')
        }),
        (_('Personal info'), {
            'fields': (('email', 'confirm_sent'), 'formated_extra_data')
        }),
        (_('Extra info'), {
            'fields': (('confirmed', 'confirmed_date'),
                       ('ntickets', 'price'),
                       'discount', 'payment')
        }),
    )

    def payment(self, obj):
        try:
            tws = TicketWindowSale.objects.get(purchase=obj)
        except:
            return '-'
        return tws.get_payment_display()
    payment.short_description = _('payment')

    def ntickets(self, obj):
        return obj.tickets.count()
    ntickets.short_description = _('ntickets')

    def twin(self, obj):
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

    def formated_extra_data(self, obj):
        extras = obj.get_extras_dict()
        html = '<table>'
        for k in sorted(extras.keys()):
            html += '<tr><th style="width: 20%">' + k + '</th><td>' + str(extras[k]) + '</td></tr>'
        html += '</table>'
        return mark_safe(html)
    formated_extra_data.short_description = _('extra data')


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
