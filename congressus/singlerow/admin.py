from django.contrib import admin

from .models import SingleRowTail


class SingleRowTailAdmin(admin.ModelAdmin):
    list_display = ('event', 'window', 'date')
    list_filter = ('event', 'window')
    search_fields = ('window',)

admin.site.register(SingleRowTail, SingleRowTailAdmin)
