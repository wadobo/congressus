from django.contrib import admin

from events.admin import GlobalEventFilter
from .models import SingleRowTail, SingleRowConfig


@admin.register(SingleRowTail)
class SingleRowTailAdmin(admin.ModelAdmin):
    list_display = ('event', 'window', 'date')
    list_filter = (GlobalEventFilter, 'window')
    search_fields = ('window',)


@admin.register(SingleRowConfig)
class SingleRowConfigAdmin(admin.ModelAdmin):
    list_display = ('event', 'last_window')
    list_filter = (GlobalEventFilter, )
    filter_horizontal = ('waiting', )
