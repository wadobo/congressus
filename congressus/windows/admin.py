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

from events.admin import GlobalEventFilter


@admin.register(TicketWindow)
class TicketWindowAdmin(admin.ModelAdmin):
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
    list_filter = (GlobalEventFilter, "location")
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ("name", "slug", "event__name")
    filter_horizontal = ("templates",)


class GlobalWindowEventFilter(GlobalEventFilter):
    title = _("Event")
    parameter_name = "window__event"


class CustomWindowFilter(admin.SimpleListFilter):
    title = _("ticket window")
    parameter_name = "window"

    def lookups(self, request, model_admin):
        windows = TicketWindow.objects.select_related("event")
        if current_event := request.session.get("current_event", None):
            windows = windows.filter(event=current_event)
        return [(str(win.id), str(win)) for win in windows]

    def queryset(self, request, queryset):
        qs = queryset.select_related("window", "window__event")
        if not self.value():
            return qs

        return qs.filter(window__event=self.value())


@admin.register(TicketWindowSale)
class TicketWindowSaleAdmin(admin.ModelAdmin):
    list_display = ("window", "user", "purchase", "price", "payment")
    list_filter = (
        GlobalWindowEventFilter,
        ("user", admin.RelatedOnlyFieldListFilter),
        "payment",
        CustomWindowFilter,
    )
    search_fields = ("window__name", "user__username", "window__event__name")
    date_hierarchy = "date"
    autocomplete_fields = ("purchase",)
    readonly_fields = ["purchase"]


@admin.register(TicketWindowCashMovement)
class TicketWindowCashMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "window", "famount", "type", "date", "note")
    list_filter = (
        GlobalWindowEventFilter,
        "type",
        CustomWindowFilter,
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
