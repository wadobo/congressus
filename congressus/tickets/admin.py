from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from django.utils import timezone
from django.utils.formats import date_format

from .models import Ticket
from .models import MultiPurchase
from .models import TicketWarning
from .models import TicketSeatHold
from admin_csv import CSVMixin

from .filters import TicketWindowFilter
from .filters import SingleTicketWindowFilter
from windows.models import TicketWindowSale
from windows.utils import online_sale


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


def mark_used(modeladmin, request, queryset):
    now = timezone.now()
    for i in queryset:
        i.used = True
        i.used_date = now
        i.save()
mark_used.short_description = _("Mark like used")


def mark_no_used(modeladmin, request, queryset):
    for i in queryset:
        i.used = False
        i.used_date = None
        i.save()
mark_no_used.short_description = _("Mark like no used")


def delete_selected(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()
delete_selected.short_description = _("Remove")

class TicketAdmin(CSVMixin, admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 800
    list_display = ('order', 'order_tpv2', 'session2', 'cseat', 'twin',
                    'created2', 'confirmed', 'used',
                    'email', 'payment', 'price2', 'event')
    list_filter = ('confirmed', 'used', SingleTicketWindowFilter, 'event_name', 'session__space')
    search_fields = ('order', 'order_tpv', 'email', 'mp__order', 'mp__order_tpv')
    date_hierarchy = 'created'
    actions = [delete_selected, confirm, unconfirm, mark_used, mark_no_used]
    csv_fields = [
        'email',

        'order',
        'order_tpv',

        'confirmed',
        'confirmed_date',

        'price2',
        'cseat',
        'mp',
        'twin',

        'event_name',
        'space_name',
        'session_name',
        'created',

        'used',
    ]

    readonly_fields = (
        'order_tpv_linked', 'order', 'event_name', 'session2', 'cseat',
        'confirmed', 'confirmed_date', 'price', 'tax',
        'email', 'formated_extra_data',
        'used_date', 'gate_name',
        'start', 'end', 'twin'
    )

    fieldsets = (
        (None, {
            'fields': ('order', 'order_tpv_linked', 'event_name',
                       'session2', 'cseat', 'twin')
        }),
        (_('Personal info'), {
            'fields': ('email', 'formated_extra_data')
        }),
        (_('Extra info'), {
            'fields': (('confirmed', 'confirmed_date'),
                       ('price', 'tax'),
                       ('used', 'used_date', 'gate_name'),
                       'start', 'end')
        }),
    )

    def formated_extra_data(self, obj):
        extras = obj.get_extras_dict()
        html = '<table>'
        for k in sorted(extras.keys()):
            html += '<tr><th style="width: 20%">' + k + '</th><td>' + str(extras[k]) + '</td></tr>'
        html += '</table>'
        return mark_safe(html)
    formated_extra_data.short_description = _('extra data')

    def order_tpv_linked(self, obj):
        if not obj.mp:
            return obj.order_tpv

        url = reverse('admin:tickets_multipurchase_change', args=(obj.mp.id,))
        html = '<a href="' + url + '">' + obj.mp.order_tpv + '</a>'
        return mark_safe(html)
    order_tpv_linked.short_description = _('order TPV')

    def price2(self, obj):
        return obj.get_real_price()
    price2.short_description = _('price')

    def twin(self, obj):
        try:
            tws = TicketWindowSale.objects.get(purchase__tickets=obj)
        except:
            return '-'
        prefix = tws.window.code
        return prefix
    twin.short_description = _('ticket window')

    def order_tpv2(self, obj):
        if obj.mp:
            return obj.mp.order_tpv
        else:
            return obj.order_tpv
    order_tpv2.short_description = _('order TPV')

    def session2(self, obj):
        return obj.session.short()
    session2.short_description = _('session')

    def payment(self, obj):
        if not obj.mp:
            return '-'
        try:
            tws = TicketWindowSale.objects.get(purchase=obj.mp)
        except:
            return '-'
        return tws.get_payment_display()
    payment.short_description = _('payment')

    def created2(self, obj):
        fmt='d/m/y H:i:s'
        d1 = timezone.localtime(obj.created)
        return date_format(d1, fmt)
    created2.short_description = _('date')


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


def link_online_sale(modeladmin, request, queryset):
    for i in queryset:
        online_sale(i)
        i.save()
link_online_sale.short_description = _("Link online sale")


class MPAdmin(CSVMixin, admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 800
    list_display = ('order_tpv', 'twin', 'created', 'confirmed2', 'email', 'ntickets', 'price', 'event')
    list_filter = ('confirmed', TicketWindowFilter, 'ev', 'tpv_error')
    search_fields = ('order', 'order_tpv', 'email', 'extra_data')
    date_hierarchy = 'created'
    actions = [delete_selected, confirm, unconfirm, link_online_sale]
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
        'tpv_error', 'tpv_error_info', 'twin'
    )

    fieldsets = (
        (None, {
            'fields': ('order_tpv', 'order', 'ev', 'twin')
        }),
        (_('Personal info'), {
            'fields': (('email', 'confirm_sent'), 'formated_extra_data')
        }),
        (_('Extra info'), {
            'fields': (('confirmed', 'confirmed_date'),
                       ('ntickets', 'price'),
                       'discount', 'payment',
                       'tpv_error', 'tpv_error_info',
                      )
        }),
    )

    def confirmed2(self, obj):
        icon = 'icon-no.svg'
        if obj.confirmed:
            icon = 'icon-yes.svg'
        elif obj.tpv_error:
            icon = 'icon-alert.svg'
        html = '<img src="{}/admin/img/{}"/>'.format(settings.STATIC_URL, icon)
        return mark_safe(html)
    confirmed2.short_description = _('confirmed')


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
        return obj.get_real_price()
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
