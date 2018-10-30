from django.contrib import admin

from .models import SingleRowTail, SingleRowConfig
from congressus.admin import register


class SingleRowTailAdmin(admin.ModelAdmin):
    list_display = ('event', 'window', 'date')
    list_filter = ('event', 'window')
    search_fields = ('window',)

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(event__slug=slug)


class SingleRowConfigAdmin(admin.ModelAdmin):
    list_display = ('event', 'last_window')
    list_filter = ('event', )
    filter_horizontal = ('waiting', )

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(event__slug=slug)


register(SingleRowTail, SingleRowTailAdmin)
register(SingleRowConfig, SingleRowConfigAdmin)
