from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from .models import InvitationGenerator
from .models import Invitation
from .models import InvitationType


def get_csv(modeladmin, request, queryset):
    csv = []
    for i, inv in enumerate(queryset):
        csv.append('%d, %s, %s' % (i+1, inv.order, inv.type.name))
    response = HttpResponse(content_type='application/csv')
    response['Content-Disposition'] = 'filename="invs.csv"'
    response.write('\n'.join(csv))
    return response
get_csv.short_description = _("Download csv")


class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'is_pass', 'start', 'end')
    list_filter = ('is_pass', 'event')
    filter_horizontal = ('sessions', 'gates')


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'type', 'is_pass', 'created', 'used', 'concept')
    list_filter = ('is_pass', 'type')
    date_hierarchy = 'created'

    # TODO, add get_A4 and get_thermal
    actions = [get_csv, ]

    def concept(self, obj):
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
