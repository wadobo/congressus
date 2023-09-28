import csv
from io import StringIO

from django.conf import settings
from django.contrib import admin
from django.db.models import Prefetch
from django.http import HttpResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from invs.filters import UsedFilter
from invs.models import (
    InvUsedInSession,
    Invitation,
    InvitationGenerator,
    InvitationType,
)
from events.admin import GlobalEventFilter
from events.models import Gate, Session, TicketTemplate
from weasyprint import HTML


class RelatedOnlyDropdownFilter(admin.RelatedOnlyFieldListFilter):
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"


@admin.action(description=_("Download CSV"))
def get_csv(modeladmin, request, queryset):
    content = StringIO()
    writer = csv.writer(content, delimiter=",")

    def fillcsv(query):
        for inv in query:
            seat_layout = ["", "", ""]
            if inv.seat_layout:
                seat_layout = [inv.seat_layout.name, inv.seat_row(), inv.seat_column()]

            row = [inv.order, inv.type.name] + seat_layout + [inv.used_date]
            writer.writerow(row)

    if modeladmin.model == InvitationGenerator:
        queryset = queryset.select_related("type").all()
        for ig in queryset:
            fillcsv(ig.invitations.all())
    else:
        queryset = (
            queryset.select_related(
                "type", "generator", "generator__type", "seat_layout"
            )
            .prefetch_related("usedin")
            .all()
        )
        fillcsv(queryset)

    response = HttpResponse(content_type="application/csv")
    response["Content-Disposition"] = 'filename="invs.csv"'
    response.write(content.getvalue().strip("\r\n"))
    return response


@admin.action(description=_("Download PDF"))
def get_pdf(modeladmin, request, queryset):
    html = ""
    if modeladmin.model == InvitationGenerator:
        for ig in queryset:
            html += ig.html_format()
    else:
        for inv in queryset:
            html += inv.html_format()
    pdfs = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="invs.pdf"'
    response.write(pdfs)
    return response


@admin.action(description=_("Download HTML"))
def get_html(modeladmin, request, queryset):
    html = ""
    if modeladmin.model == InvitationGenerator:
        for ig in queryset:
            html += ig.html_format()
    else:
        for inv in queryset:
            html += inv.html_format()
    return HttpResponse(html)


@admin.register(InvitationType)
class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "is_pass", "start", "end")
    list_filter = (GlobalEventFilter, "is_pass")
    filter_horizontal = ("sessions", "gates")

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "template":
            field.queryset = TicketTemplate.objects.all().order_by("name")

        return field

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        current_event = request.session.get("current_event", None)
        if db_field.name == "gates" and current_event:
            kwargs["queryset"] = Gate.objects.filter(event=current_event).order_by(
                "name"
            )

        if db_field.name == "sessions" and current_event:
            kwargs["queryset"] = (
                Session.objects.filter(space__event=current_event)
                .with_space()
                .order_by("name")
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class InvUsedInSessionInline(admin.TabularInline):
    model = InvUsedInSession
    fields = ("session", "date")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class GlobalTypeEventFilter(GlobalEventFilter):
    parameter_name = "type__event"


class GeneratorFilter(admin.SimpleListFilter):
    title = _("Generator")
    parameter_name = "generator"

    def lookups(self, request, model_admin):
        generators = InvitationGenerator.objects.select_related("type", "type__event")
        if current_event := request.session.get("current_event", None):
            generators = generators.filter(type__event=current_event)
        return [(str(gen.id), str(gen)) for gen in generators]

    def queryset(self, request, queryset):
        qs = queryset.select_related("type")
        if not self.value():
            return qs

        return qs.filter(generator=self.value())


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("order", "type", "is_pass", "created", "iused", "concept", "cseat")
    date_hierarchy = "created"
    search_fields = ("order", "generator__concept", "name")

    list_filter = (
        GlobalTypeEventFilter,
        "is_pass",
        UsedFilter,
        ("type", RelatedOnlyDropdownFilter),
        GeneratorFilter,
    )

    actions = [get_csv, get_pdf, get_html]
    inlines = [InvUsedInSessionInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if event := request.session.get("current_event", None):
            form.base_fields["type"].queryset = InvitationType.objects.filter(
                event=event
            )
            form.base_fields["generator"].queryset = InvitationGenerator.objects.filter(
                type__event=event
            )
        return form

    def get_queryset(self, request):
        from events.models import Session

        qs = super().get_queryset(request)
        return qs.select_related(
            "generator",
            "generator__type",
            "generator__type__template",
            "generator__type__event",
            "type",
            "type__event",
            "type__template",
            "seat_layout",
        ).prefetch_related(
            Prefetch(
                "type__sessions",
                queryset=Session.objects.select_related(
                    "template",
                    "window_template",
                    "space",
                    "space__event",
                ),
            ),
            "type__gates",
            "generator__type__gates",
            Prefetch(
                "generator__type__sessions",
                queryset=Session.objects.select_related(
                    "template",
                    "window_template",
                    "space",
                    "space__event",
                ),
            ),
            Prefetch(
                "usedin",
                queryset=InvUsedInSession.objects.select_related(
                    "session",
                    "session__template",
                    "session__window_template",
                    "session__space",
                    "session__space__event",
                ),
            ),
        )

    def concept(self, obj):
        if not obj.generator:
            return "-"
        return obj.generator.concept or "-"

    def iused(self, obj):
        return obj.used

    iused.short_description = _("used")
    iused.boolean = True

    def used_at(self, obj):
        if not obj.used_date:
            return "-"
        fmt = "d/m/y H:i:s"
        d1 = timezone.localtime(obj.used_date)
        return date_format(d1, fmt)

    used_at.short_description = _("used at")


@admin.register(InvitationGenerator)
class InvitationGeneratorAdmin(admin.ModelAdmin):
    list_display = ("type", "amount", "price", "concept", "created")
    actions = [get_csv, get_pdf, get_html]
    list_filter = (GlobalTypeEventFilter,)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if event := request.session.get("current_event", None):
            form.base_fields["type"].queryset = InvitationType.objects.filter(
                event=event
            )
        return form

    class Media:
        js = [
            settings.STATIC_URL + "js/jquery.min.js",
            settings.STATIC_URL + "js/invitation.js",
        ]
