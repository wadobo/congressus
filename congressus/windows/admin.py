from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import TicketWindow
from .models import TicketWindowSale
from .models import TicketWindowCashMovement

from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

from extended_filters.filters import CheckBoxListFilter
from extended_filters.filters import DateRangeFilter


class TicketWindowAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'slug', 'event', 'location', 'online')
    list_filter = ('event', 'location')
    search_fields = ('name', 'slug', 'event__name')


class TicketWindowSaleAdmin(admin.ModelAdmin):
    list_display = ('window', 'user', 'purchase', 'price', 'payment')
    list_filter = ('user', 'payment', 'window', 'window__event')
    search_fields = ('window__name', 'user__username', 'window__event__name')
    date_hierarchy = 'date'


class TicketWindowCashMovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'day', 'window', 'famount', 'type', 'date', 'note')
    list_filter = ('type', ('window', CheckBoxListFilter), ('date', DateRangeFilter))
    search_fields = ('window__name', )
    date_hierarchy = 'date'

    readonly_fields = ('date', 'id', 'day')

    fieldsets = (
        (None, {
            'fields': ('id', ('date', 'day'),
                       'window', 'amount', 'type', 'note')
        }),
    )

    def day(self, obj):
        d1 = timezone.localtime(obj.date)
        return date_format(d1, 'l')
    day.short_description = _('day')

    def famount(self, obj):
        css = 'text-align: right;'
        amn = obj.amount
        if obj.type == 'change':
            css += 'color: red'
            amn = -amn
        elif obj.type == 'return':
            css += 'color: blue'

        html = '<div style="{}">{}</div>'.format(css, amn)
        return mark_safe(html)
    famount.short_description = _('amount')


admin.site.register(TicketWindow, TicketWindowAdmin)
admin.site.register(TicketWindowSale, TicketWindowSaleAdmin)
admin.site.register(TicketWindowCashMovement, TicketWindowCashMovementAdmin)
