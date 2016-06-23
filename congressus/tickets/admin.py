from django.contrib import admin

from .models import Invitation
from .models import InvitationType
from .models import Pass
from .models import PassType
from .models import Ticket
from .models import MultiPurchase
from .models import TicketWarning
from .models import TicketSeatHold
from admin_csv import CSVMixin


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'created', 'seat', 'seat_layout', 'type', 'used')


class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end')


class PassAdmin(admin.ModelAdmin):
    list_display = ('order', 'created', 'seat', 'seat_layout', 'type', 'used')


class PassTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end')


class TicketAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event', 'confirmed', 'email', 'session', 'price', 'cseat', 'mp')
    list_filter = ('confirmed',)
    search_fields = ('order', 'order_tpv', 'email', 'mp__order')
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

    def price(self, obj):
        return obj.get_price()

    def eventname(self, obj):
        return obj.event().name

    def spacename(self, obj):
        return obj.space().name

    def sessionname(self, obj):
        return obj.session.name

    def invcode(self, obj):
        return obj.inv.code if obj.inv else ''


class MPAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event', 'confirmed', 'email', 'ntickets')
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
        'created',
    ]

    def ntickets(self, obj):
        return obj.tickets.count()

    def eventname(self, obj):
        return obj.event.name

    def invcode(self, obj):
        return obj.inv.code if obj.inv else ''


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
admin.site.register(Pass, PassAdmin)
admin.site.register(PassType, PassTypeAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketWarning, TicketWarningAdmin)
admin.site.register(MultiPurchase, MPAdmin)
admin.site.register(TicketSeatHold, TicketSeatHoldAdmin)
admin.site.index_template = 'admin/generator.html'
