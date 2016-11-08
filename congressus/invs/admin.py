from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from .models import InvitationGenerator
from .models import Invitation
from .models import InvitationType
from .models import InvUsedInSession

from tickets.utils import concat_pdf
from tickets.utils import generate_pdf
from tickets.utils import generate_thermal


def get_csv(modeladmin, request, queryset):
    csv = []

    def fillcsv(q):
        for i, inv in enumerate(q):
            row = '%d, %s, %s' % (i+1, inv.order, inv.type.name)
            if inv.seat:
                row += ',%s, %s, %s' % (inv.seat_layout.name, inv.seat_row(), inv.seat_column())
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
            files.append(generate_pdf(inv, asbuf=True, inv=True))

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
            files.append(generate_thermal(inv, asbuf=True, inv=True))

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


class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'is_pass', 'start', 'end')
    list_filter = ('is_pass', 'event')
    filter_horizontal = ('sessions', 'gates')


class InvUsedInSessionInline(admin.TabularInline):
    model = InvUsedInSession
    fields = ('session', 'date')
    readonly_fields = fields

    def has_add_permission(self, request):
        return False


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'type', 'is_pass', 'created', 'iused', 'concept', 'name')
    list_filter = ('is_pass', 'type')
    date_hierarchy = 'created'
    search_fields = ('order',)

    actions = [get_csv, get_pdf, get_thermal]
    inlines = [InvUsedInSessionInline]

    def concept(self, obj):
        if not obj.generator:
            return '-'
        return obj.generator.concept or '-'

    def iused(self, obj):
        return obj.used
    iused.short_description = _('used')
    iused.boolean = True


class InvitationGeneratorAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'price', 'concept', 'created')
    actions = [get_csv, get_pdf, get_thermal]

    class Media:
        js = [
                settings.STATIC_URL + 'js/jquery.min.js',
                settings.STATIC_URL + 'js/invitation.js',
        ]

admin.site.register(InvitationGenerator, InvitationGeneratorAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(InvitationType, InvitationTypeAdmin)
