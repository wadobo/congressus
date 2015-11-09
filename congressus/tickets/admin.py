from django.contrib import admin

from .models import Event, Ticket, InvCode
from .models import ConfirmEmail, EmailAttachment


class InvCodeInline(admin.TabularInline):
    model = InvCode


class EventAdmin(admin.ModelAdmin):
    inlines = [InvCodeInline]
    list_display = ('name', 'start', 'end', 'active', 'price')
    list_filter = ('active',)
    date_hierarchy = 'start'


class InvCodeAdmin(admin.ModelAdmin):
    list_display = ('event', 'person', 'code', 'used')
    list_filter = ('event', 'used')
    search_fields = ('event', 'person', 'code')


class TicketAdmin(admin.ModelAdmin):
    list_display = ('order', 'order_tpv', 'event', 'confirmed', 'name', 'email', 'type', 'food')
    list_filter = ('confirmed', 'food', 'type')
    search_fields = ('order', 'order_tpv', 'email')
    date_hierarchy = 'created'


class Attachments(admin.TabularInline):
    model = EmailAttachment


class ConfirmEmailAdmin(admin.ModelAdmin):
    inlines = [Attachments]
    list_display = ('event', 'subject')
    list_filter = ('event',)
    search_fields = ('event', 'subject', 'body')


admin.site.register(Event, EventAdmin)
admin.site.register(InvCode, InvCodeAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(ConfirmEmail, ConfirmEmailAdmin)
