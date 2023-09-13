import csv
from io import StringIO

from django import forms
from django.db.models import Prefetch
from django.conf import settings
from django.contrib import admin
from django.contrib.flatpages.admin import FlatpageForm, FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from extended_filters.filters import DateRangeFilter
from tinymce.widgets import TinyMCE

from events.admin import GlobalEventFilter
from events.admin import CustomSpaceFilter
from events.models import TicketField
from tickets.filters import TicketWindowFilter, SessionFilter, SingleTicketWindowFilter
from tickets.models import (
    MultiPurchase,
    Ticket,
    TicketSeatHold,
    TicketWarning,
)
from windows.models import TicketWindowSale
from windows.utils import online_sale


CACHE_TICKET_FIELDS = {
    tf.id: tf.label
    for tf in TicketField.objects.filter(pk__in=settings.CSV_TICKET_FIELDS)
}


def confirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirm()


confirm.short_description = _("Manual confirm")


def unconfirm(modeladmin, request, queryset):
    for i in queryset:
        i.confirmed = False
        i.remove_hold_seats()
        i.save()


unconfirm.short_description = _("Manual unconfirm")


def get_csv(modeladmin, request, queryset):
    csv_fields = [
        "email",
        "order",
        "order_tpv",
        "confirmed",
        "confirmed_date",
        "price",
        "num_tickets",
        "ticket_window_code",
        "payment_method",
        "ev",
        "created",
    ]
    extra_data = queryset[0].ev.ticket_fields() if len(queryset) else []
    header = [_(field) for field in csv_fields + extra_data]

    content = StringIO()
    writer = csv.writer(content, delimiter=",")
    writer.writerow(header)

    for mp in queryset:
        row = [str(getattr(mp, field)) for field in csv_fields]
        row += [mp.get_extra_data(label) for label in extra_data]
        writer.writerow(row)

    response = HttpResponse(content_type="application/csv")
    response["Content-Disposition"] = 'filename="compras_multiples.csv"'
    response.write(content.getvalue().strip("\r\n"))
    return response


get_csv.short_description = _("Download csv")


def get_csv_tickets(modeladmin, request, queryset):
    csv_fields = [
        "email",
        "order",
        "order_tpv",
        "confirmed",
        "confirmed_date",
        "get_real_price",
        "cseat",
        "mp",
        "event_name",
        "space_name",
        "session_name",
        "created",
        "used",
        "extra_data",
    ]
    # ] + ['ticket_field_' + i for i in settings.CSV_TICKET_FIELDS]

    qs = modeladmin.get_queryset(request)
    header = [_(field) for field in csv_fields]

    content = StringIO()
    writer = csv.writer(content, delimiter=",")
    writer.writerow(header)

    for ticket in qs:
        row = [str(getattr(ticket, field)) for field in csv_fields]
        writer.writerow(row)

    response = HttpResponse(content_type="application/csv")
    response["Content-Disposition"] = 'filename="tickets.csv"'
    response.write(content.getvalue().strip("\r\n"))
    return response


get_csv_tickets.short_description = _("Download csv")


class GlobalMPEventFilter(GlobalEventFilter):
    parameter_name = "mp__ev"


class CustomSessionSpaceFilter(CustomSpaceFilter):
    title = _("space")
    parameter_name = "space"

    def queryset(self, request, queryset):
        qs = queryset.select_related("session__space", "session__space__event")
        if not self.value():
            return qs

        return qs.filter(session__space=self.value())


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 800
    list_display = (
        "order",
        "order_tpv2",
        "session2",
        "cseat",
        "twin",
        "created2",
        "confirmed",
        "used",
        "email",
        "payment",
        "payment_method",
        "price2",
        "event",
    )
    list_filter = (
        GlobalMPEventFilter,
        ("created", DateRangeFilter),
        "confirmed",
        "payment_method",
        "used",
        SingleTicketWindowFilter,
        "seat_layout",
        SessionFilter,
        CustomSessionSpaceFilter,
    )
    search_fields = (
        "order",
        "order_tpv",
        "email",
        "mp__order",
        "mp__order_tpv",
        "seat",
    )
    date_hierarchy = "created"
    actions = [confirm, unconfirm, "mark_used", "mark_no_used", get_csv_tickets]

    readonly_fields = (
        "order_tpv_linked",
        "order",
        "event_name",
        "session2",
        "cseat",
        "confirmed",
        "confirmed_date",
        "price",
        "tax",
        "email",
        "formated_extra_data",
        "used_date",
        "gate_name",
        "start",
        "end",
        "twin",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "order_tpv_linked",
                    "event_name",
                    "session2",
                    "cseat",
                    "twin",
                )
            },
        ),
        (_("Personal info"), {"fields": ("email", "formated_extra_data")}),
        (
            _("Extra info"),
            {
                "fields": (
                    ("confirmed", "confirmed_date"),
                    ("price", "tax"),
                    ("used", "used_date", "gate_name"),
                    "start",
                    "end",
                )
            },
        ),
    )
    csv_fields = [
        "email",
        "order",
        "order_tpv",
        "confirmed",
        "confirmed_date",
        "price2",
        "cseat",
        "mp",
        "twin",
        "event_name",
        "space_name",
        "session_name",
        "created",
        "used",
        "used_at",
    ] + ["ticket_field_" + i for i in settings.CSV_TICKET_FIELDS]

    def __getattr__(self, value):
        if value.startswith("ticket_field_"):
            label = CACHE_TICKET_FIELDS.get(value.split("_")[-1])

            def f(obj):
                return obj.get_extra_data(label)

            f.short_description = label
            return f
        raise AttributeError

    def formated_extra_data(self, obj):
        extras = obj.get_extras_dict()
        html = "<table>"
        for k in sorted(extras.keys()):
            html += (
                '<tr><th style="width: 20%">'
                + k
                + "</th><td>"
                + str(extras[k])
                + "</td></tr>"
            )
        html += "</table>"
        return mark_safe(html)

    formated_extra_data.short_description = _("extra data")

    def order_tpv_linked(self, obj):
        if not obj.mp:
            return obj.order_tpv

        url = reverse("admin:tickets_multipurchase_change", args=(obj.mp.id,))
        html = '<a href="' + url + '">' + obj.mp.order_tpv + "</a>"
        return mark_safe(html)

    order_tpv_linked.short_description = _("order TPV")

    def price2(self, obj):
        return obj.get_real_price()

    price2.short_description = _("price")

    def twin(self, obj):
        try:
            tws = obj.mp.sales.all()[0]
        except Exception:
            return "-"
        prefix = tws.window.code
        return prefix

    twin.short_description = _("ticket window")

    def order_tpv2(self, obj):
        if obj.mp:
            return obj.mp.order_tpv
        else:
            return obj.order_tpv

    order_tpv2.short_description = _("order TPV")

    def session2(self, obj):
        return obj.session.short()

    session2.short_description = _("session")

    def payment(self, obj):
        if not obj.mp:
            return "-"
        try:
            tws = obj.mp.sales.all()[0]
        except Exception:
            return "-"
        return tws.get_payment_display()

    payment.short_description = _("payment")

    def created2(self, obj):
        fmt = "d/m/y H:i:s"
        d1 = timezone.localtime(obj.created)
        return date_format(d1, fmt)

    created2.short_description = _("date")

    def used_at(self, obj):
        if not obj.used_date:
            return "-"
        fmt = "d/m/y H:i:s"
        d1 = timezone.localtime(obj.used_date)
        return date_format(d1, fmt)

    used_at.short_description = _("used at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "seat_layout",
                "session",
                "session__space",
                "session__space__event",
                "session__template",
                "mp",
                "mp__ev",
            )
            .prefetch_related(
                Prefetch(
                    "mp__sales",
                    queryset=TicketWindowSale.objects.select_related("window"),
                ),
            )
        )

    def mark_used(self, request, queryset):
        now = timezone.now()
        for i in queryset:
            i.used = True
            i.used_date = now
            i.save()

    mark_used.short_description = _("Mark like used")

    def mark_no_used(self, request, queryset):
        for i in queryset:
            i.used = False
            i.used_date = None
            i.save()

    mark_no_used.short_description = _("Mark like no used")


class TicketInline(admin.TabularInline):
    model = Ticket
    fields = ("link_order", "session", "price", "seat_layout", "seat")
    readonly_fields = fields

    def link_order(self, obj):
        url = reverse("admin:tickets_ticket_change", args=(obj.id,))
        html = '<a href="' + url + '">' + obj.order + "</a>"
        return mark_safe(html)

    link_order.short_description = _("order")

    def has_delete_permission(self, request, obj):
        return False

    def has_add_permission(self, request, obj=None):
        return False


def link_online_sale(modeladmin, request, queryset):
    for i in queryset:
        online_sale(i)
        i.save()


link_online_sale.short_description = _("Link online sale")


class GlobalEvFilter(GlobalEventFilter):
    parameter_name = "ev"


@admin.register(MultiPurchase)
class MPAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 800
    list_display = (
        "order_tpv",
        "ticket_window_code",
        "created",
        "confirmed2",
        "email",
        "num_tickets",
        "price",
        "payment_method",
        "event",
    )
    list_filter = (
        GlobalEvFilter,
        ("created", DateRangeFilter),
        "confirmed",
        "payment_method",
        TicketWindowFilter,
        "tpv_error",
    )

    search_fields = ("order", "order_tpv", "email", "extra_data")
    date_hierarchy = "created"
    actions = [confirm, unconfirm, link_online_sale, get_csv]
    inlines = [
        TicketInline,
    ]

    def __getattr__(self, value):
        if value.startswith("ticket_field_"):
            label = CACHE_TICKET_FIELDS.get(value.split("_")[-1])

            def f(obj):
                return obj.get_extra_data(label)

            f.short_description = label
            return f
        raise AttributeError

    readonly_fields = (
        "order_tpv",
        "order",
        "ev",
        "confirmed",
        "confirmed_date",
        "num_tickets",
        "real_price",
        "payment",
        "formated_extra_data",
        "tpv_error",
        "tpv_error_info",
        "ticket_window_code",
        "created",
    )

    fieldsets = (
        (
            None,
            {"fields": ("order_tpv", "order", "ev", "ticket_window_code", "created")},
        ),
        (
            _("Personal info"),
            {"fields": (("email", "confirm_sent"), "formated_extra_data")},
        ),
        (
            _("Extra info"),
            {
                "fields": (
                    ("confirmed", "confirmed_date"),
                    ("num_tickets", "real_price"),
                    "discount",
                    "payment",
                    "payment_method",
                    "tpv_error",
                    "tpv_error_info",
                )
            },
        ),
    )

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def confirmed2(self, obj):
        icon = "icon-no.svg"
        if obj.confirmed:
            icon = "icon-yes.svg"
        elif obj.tpv_error:
            icon = "icon-alert.svg"
        html = '<img src="{}/admin/img/{}"/>'.format(settings.STATIC_URL, icon)
        return mark_safe(html)

    confirmed2.short_description = _("confirmed")

    def payment(self, obj):
        tws = obj.sales.all()
        if not tws:
            return "-"
        return tws[0].get_payment_display()

    payment.short_description = _("payment")

    def formated_extra_data(self, obj):
        extras = obj.get_extras_dict()
        html = "<table>"
        for k in sorted(extras.keys()):
            html += (
                '<tr><th style="width: 20%">'
                + k
                + "</th><td>"
                + str(extras[k])
                + "</td></tr>"
            )
        html += "</table>"
        return mark_safe(html)

    formated_extra_data.short_description = _("extra data")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("ev", "discount")
            .prefetch_related(
                Prefetch(
                    "sales", queryset=TicketWindowSale.objects.select_related("window")
                ),
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "session", "session__template", "session__space"
                    ).order_by("session__start"),
                ),
            )
        )


@admin.register(TicketWarning)
class TicketWarningAdmin(admin.ModelAdmin):
    list_display = ("name", "ev", "csessions1", "csessions2", "message")
    list_filter = ("name",)
    filter_horizontal = ("sessions1", "sessions2")

    def csessions1(self, obj):
        return ", ".join(str(s) for s in obj.sessions1.all())

    def csessions2(self, obj):
        return ", ".join(str(s) for s in obj.sessions2.all())


@admin.register(TicketSeatHold)
class TicketSeatHoldAdmin(admin.ModelAdmin):
    search_fields = ("client",)
    date_hierarchy = "date"
    list_display = ("client", "session", "layout", "seat", "date", "type")
    list_filter = (
        ("session", admin.RelatedOnlyFieldListFilter),
        "type",
        ("layout", admin.RelatedOnlyFieldListFilter),
    )


# tinymce for flatpages
class PageForm(FlatpageForm):
    content = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = FlatPage
        fields = ["content"]


class PageAdmin(FlatPageAdmin):
    form = PageForm


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, PageAdmin)
