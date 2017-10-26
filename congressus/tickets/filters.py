from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from windows.models import TicketWindow


class TicketWindowFilter(admin.SimpleListFilter):
    title = _('Window ticket')
    parameter_name = 'twin'

    def lookups(self, request, model_admin):
        ws = [(w.id, '%s - %s' % (w.event, w.name)) for w in TicketWindow.objects.all()]
        ws = [('--', _('without ticket window'))] + ws
        return ws

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() != '--':
            return queryset.filter(sales__window__id=self.value())
        else:
            return queryset.filter(sales__window=None)


class SingleTicketWindowFilter(TicketWindowFilter):
    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() != '--':
            return queryset.filter(mp__sales__window__id=self.value())
        else:
            return queryset.filter(mp__sales__window=None)
