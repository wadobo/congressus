from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Invitation
from .models import InvitationType
from .models import Ticket
from .models import MultiPurchase
from .models import TicketWarning
from .models import TicketSeatHold
from admin_csv import CSVMixin


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'created', 'seat', 'seat_layout', 'type', 'used', 'is_pass')
    list_filter = ('is_pass', )


class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ('session', 'name', 'start', 'end')


def confirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirmed = True
        i.save()
confirm.short_description = _("Manual confirm")


def unconfirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirmed = False
        i.save()
unconfirm.short_description = _("Manual unconfirm")


class TicketAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event_name', 'confirmed', 'email', 'session', 'price', 'cseat', 'mp', 'twin')
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
    list_display = ('client', 'session',  'layout', 'seat', 'date')
    list_filter = ('session',)


admin.site.register(Invitation, InvitationAdmin)
admin.site.register(InvitationType, InvitationTypeAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketWarning, TicketWarningAdmin)
admin.site.register(MultiPurchase, MPAdmin)
admin.site.register(TicketSeatHold, TicketSeatHoldAdmin)
