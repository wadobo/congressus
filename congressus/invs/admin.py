from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from .models import InvitationGenerator
from .models import Invitation
from .models import InvitationType

from tickets.utils import concat_pdf
from tickets.utils import generate_pdf
from tickets.utils import generate_thermal


def get_csv(modeladmin, request, queryset):
    csv = []
    for i, inv in enumerate(queryset):
        row = '%d, %s, %s' % (i+1, inv.order, inv.type.name)
        if inv.seat:
            row += ',%s, %s, %s' % (inv.seat_layout.name, inv.seat_row(), inv.seat_column())
        csv.append(row)
    response = HttpResponse(content_type='application/csv')
    response['Content-Disposition'] = 'filename="invs.csv"'
    response.write('\n'.join(csv))
    return response
get_csv.short_description = _("Download csv")


def get_pdf(modeladmin, request, queryset):
    files = []

    for inv in queryset:
        files.append(generate_pdf(inv, asbuf=True, inv=True))
    pdfs = concat_pdf(files)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="invs.pdf"'
    response.write(pdfs)
    return response
get_pdf.short_description = _("Download A4")


def get_thermal(modeladmin, request, queryset):
    files = []

    for inv in queryset:
        files.append(generate_thermal(inv, asbuf=True, inv=True))
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


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'type', 'is_pass', 'created', 'used', 'concept')
    list_filter = ('is_pass', 'type')
    date_hierarchy = 'created'
    search_fields = ('order',)

    # TODO, add get_A4 and get_thermal
    actions = [get_csv, get_pdf, get_thermal]

    def concept(self, obj):
        if not obj.generator:
            return '-'
        return obj.generator.concept or '-'


class InvitationGeneratorAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'price', 'concept', 'created')

    class Media:
        js = [
                settings.STATIC_URL + 'js/jquery.min.js',
                settings.STATIC_URL + 'js/invitation.js',
        ]

admin.site.register(InvitationGenerator, InvitationGeneratorAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(InvitationType, InvitationTypeAdmin)
