from django.contrib import admin

from .models import InvitationGenerator
from .models import Invitation
from .models import InvitationType


class InvitationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'is_pass', 'start', 'end')
    list_filter = ('is_pass', 'event')
    filter_horizontal = ('sessions', 'gates')


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('order', 'type', 'created', 'used', 'concept')

    def concept(self, obj):
        return obj.generator.concept or '-'


class InvitationGeneratorAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'price', 'concept', 'created')


admin.site.register(InvitationGenerator, InvitationGeneratorAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(InvitationType, InvitationTypeAdmin)
