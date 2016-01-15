from django.contrib import admin

from .models import Event, Ticket, InvCode
from .models import ConfirmEmail, EmailAttachment
from .models import TShirt
from admin_csv import CSVMixin


class InvCodeInline(admin.TabularInline):
    model = InvCode


class EventAdmin(admin.ModelAdmin):
    inlines = [InvCodeInline]
    list_display = ('name', 'start', 'end', 'active', 'price', 'max', 'sold')
    list_filter = ('active',)
    date_hierarchy = 'start'

    def sold(self, obj):
        return obj.sold()


class InvCodeAdmin(admin.ModelAdmin):
    list_display = ('event', 'person', 'code', 'type', 'used')
    list_filter = ('event', 'used', 'type')
    search_fields = ('event', 'person', 'code')


class TShirts(admin.TabularInline):
    model = TShirt


class TicketAdmin(CSVMixin, admin.ModelAdmin):
    inlines = [TShirts]
    list_display = ('order', 'order_tpv', 'event', 'confirmed', 'name',
                    'email', 'type', 'food', 'tshirts')
    list_filter = ('tshirt__size', 'confirmed', 'food', 'type')
    search_fields = ('order', 'order_tpv', 'email')
    date_hierarchy = 'created'
    csv_fields = [
        'email',
        'name',
        'org',
        'confirmed',
        'tshirts',

        'invcode',
        'order',
        'order_tpv',

        'type',
        'food',
        'comments',
        'arrival',
        'departure',

        'confirmed_date',
        'confirm_sent',

        'eventname',
        'created',
    ]

    def tshirts(self, obj):
        return obj.tshirt_size()

    def eventname(self, obj):
        return obj.event.name

    def invcode(self, obj):
        return obj.inv.code if obj.inv else ''


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = ('event',)
    search_fields = ('event', 'subject', 'body')


class TShirtAdmin(admin.ModelAdmin):
    list_display = ('event', 'ticket', 'size', 'type', 'email', 'name', 'confirmed')
    list_filter = ('size', 'type', 'ticket__confirmed')
    search_fields = ('ticket', 'size', 'type')

    def confirmed(self, obj):
        return obj.ticket.confirmed
    confirmed.boolean = True

    def event(self, obj):
        return obj.ticket.event

    def email(self, obj):
        return obj.ticket.email

    def name(self, obj):
        return obj.ticket.name


admin.site.register(Event, EventAdmin)
admin.site.register(InvCode, InvCodeAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(ConfirmEmail, ConfirmEmailAdmin)
admin.site.register(TShirt, TShirtAdmin)
