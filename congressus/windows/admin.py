from django.db.models import Q
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TicketWindow
from .models import TicketWindowSale
from .models import TicketWindowCashMovement

from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

from extended_filters.filters import DateRangeFilter

from congressus.admin import register
from events.admin import EventMixin, EVFilter


class TicketWindowAdmin(EventMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "slug",
        "event",
        "location",
        "online",
        "singlerow",
        "singlerow_pos",
        "user",
    )
    list_filter = (EVFilter, "location")
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ("name", "slug", "event__name")
    filter_horizontal = ("templates",)


class TicketWindowSaleAdmin(admin.ModelAdmin):
    list_display = ("window", "user", "purchase", "price", "payment")
    list_filter = (
        ("user", admin.RelatedOnlyFieldListFilter),
        "payment",
        ("window", admin.RelatedOnlyFieldListFilter),
        ("window__event", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("window__name", "user__username", "window__event__name")
    date_hierarchy = "date"
    autocomplete_fields = ("purchase",)

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(window__event__slug=slug)

    def event_filter_fields(self, slug):
        return {
            "window": Q(event__slug=slug),
            "purchase": Q(ev__slug=slug),
        }


class TicketWindowCashMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "window", "famount", "type", "date", "note")
    list_filter = (
        "type",
        ("window", admin.RelatedOnlyFieldListFilter),
        ("date", DateRangeFilter),
    )
    search_fields = ("window__name",)
    date_hierarchy = "date"

    readonly_fields = ("date", "id", "day")

    fieldsets = (
        (None, {"fields": ("id", ("date", "day"), "window", "amount", "type", "note")}),
    )

    def day(self, obj):
        d1 = timezone.localtime(obj.date)
        return date_format(d1, "l")

    day.short_description = _("day")

    def famount(self, obj):
        css = "text-align: right;"
        amn = obj.amount
        if obj.type == "change":
            css += "color: red"
            amn = -amn
        elif obj.type == "return":
            css += "color: blue"

        html = '<div style="{}">{}</div>'.format(css, amn)
        return mark_safe(html)

    famount.short_description = _("amount")

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(window__event__slug=slug)

    def event_filter_fields(self, slug):
        return {
            "window": Q(event__slug=slug),
        }


register(TicketWindow, TicketWindowAdmin)
register(TicketWindowSale, TicketWindowSaleAdmin)
register(TicketWindowCashMovement, TicketWindowCashMovementAdmin)
