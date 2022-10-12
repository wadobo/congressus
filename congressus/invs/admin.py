from admin_csv import CSVMixin
from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import ugettext_lazy as _

from .filters import UsedFilter
from invs.models import (
    InvUsedInSession,
    Invitation,
    InvitationGenerator,
    InvitationType,
)
from congressus.admin import register
from events.admin import EventMixin, EVFilter
from events.ticket_html import TicketHTML
from events.ticket_pdf import TicketPDF
from events.models import TicketTemplate
from tickets.utils import concat_pdf


class RelatedOnlyDropdownFilter(admin.RelatedOnlyFieldListFilter):
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'


def get_csv(modeladmin, request, queryset):
    csv = []

    def fillcsv(q):
        for i, inv in enumerate(q):
            row = '%d,%s,%s' % (i+1, inv.order, inv.type.name)
            if inv.seat:
                row += ',%s,%s,%s' % (inv.seat_layout.name, inv.seat_row(), inv.seat_column())
            csv.append(row)

    if modeladmin.model == InvitationGenerator:
        for ig in queryset:
            fillcsv(ig.invitations.all())
    else:
        fillcsv(queryset)

    response = HttpResponse(content_type='application/csv')
    response['Content-Disposition'] = 'filename="invs.csv"'
    response.write('\n'.join(csv))
    return response
get_csv.short_description = _("Download csv")


def get_pdf(modeladmin, request, queryset):
    files = []

    def fillfiles(q):
        for inv in q:
            pdf = TicketPDF(inv, True).generate(asbuf=True)
            files.append(pdf)

    if modeladmin.model == InvitationGenerator:
        for ig in queryset:
            fillfiles(ig.invitations.all())
    else:
        fillfiles(queryset)

    pdfs = concat_pdf(files)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="invs.pdf"'
    response.write(pdfs)
    return response
get_pdf.short_description = _("Download A4")


def get_thermal(modeladmin, request, queryset):
    files = []

    def fillfiles(q):
        for inv in q:
            pdf = TicketPDF(inv, True).generate(asbuf=True)
            files.append(pdf)

    if modeladmin.model == InvitationGenerator:
        for ig in queryset:
            fillfiles(ig.invitations.all())
    else:
        fillfiles(queryset)

    pdfs = concat_pdf(files)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="invs.pdf"'
    response.write(pdfs)
    return response
get_thermal.short_description = _("Download thermal")


def get_html(modeladmin, request, queryset):
    invs = []
    if modeladmin.model == InvitationGenerator:
        invs = [list(ig.invitations.all()) for ig in queryset]
    else:
        invs = queryset

    return HttpResponse(TicketHTML(invs, is_invitation=True).generate())
get_html.short_description = _("Download HTML")



class InvitationTypeAdmin(EventMixin, admin.ModelAdmin):
    list_display = ('name', 'event', 'is_pass', 'start', 'end')
    list_filter = ('is_pass', EVFilter)
    filter_horizontal = ('sessions', 'gates')

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'template':
            field.queryset = TicketTemplate.objects.all().order_by('name')
        return field

    def event_filter_fields(self, slug):
        f = super().event_filter_fields(slug)
        f.update({
            "sessions": Q(space__event__slug=slug),
            "gates": Q(event__slug=slug)
        })
        return f


class InvUsedInSessionInline(admin.TabularInline):
    model = InvUsedInSession
    fields = ('session', 'date')
    readonly_fields = fields

    def has_add_permission(self, request):
        return False


class InvitationAdmin(CSVMixin, admin.ModelAdmin):
    list_display = ('order', 'type', 'is_pass', 'created', 'iused', 'concept', 'cseat')
    date_hierarchy = 'created'
    search_fields = ('order', 'generator__concept', 'name')

    list_filter = (
        'is_pass', UsedFilter,
        ('type__event', admin.RelatedOnlyFieldListFilter),
        ('type', RelatedOnlyDropdownFilter),
        ('generator', RelatedOnlyDropdownFilter),
    )

    actions = [get_csv, get_pdf, get_thermal, get_html]
    inlines = [InvUsedInSessionInline]

    csv_fields = [
        'order',
        'type',
        'is_pass',
        'created',
        'iused',
        'concept',
        'cseat',
        'used_at',
    ]

    def concept(self, obj):
        if not obj.generator:
            return '-'
        return obj.generator.concept or '-'

    def iused(self, obj):
        return obj.used
    iused.short_description = _('used')
    iused.boolean = True

    def used_at(self, obj):
        if not obj.used_date:
            return '-'
        fmt='d/m/y H:i:s'
        d1 = timezone.localtime(obj.used_date)
        return date_format(d1, fmt)
    used_at.short_description = _('used at')

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(type__event__slug=slug)

    def event_filter_fields(self, slug):
        return {
            'type': Q(event__slug=slug),
            'generator': Q(type__event__slug=slug),
        }


class InvitationGeneratorAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'price', 'concept', 'created')
    actions = [get_csv, get_pdf, get_thermal, get_html]

    class Media:
        js = [
                settings.STATIC_URL + 'js/jquery.min.js',
                settings.STATIC_URL + 'js/invitation.js',
        ]

    def event_filter(self, request, slug):
        qs = super().get_queryset(request)
        return qs.filter(type__event__slug=slug)

    def event_filter_fields(self, slug):
        return { 'type': Q(event__slug=slug), }


register(InvitationGenerator, InvitationGeneratorAdmin)
register(Invitation, InvitationAdmin)
register(InvitationType, InvitationTypeAdmin)
