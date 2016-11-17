from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class UsedFilter(admin.SimpleListFilter):
    title = _('Used')
    parameter_name = 'used'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Yes')),
            ('no', _('No')),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() == 'yes':
            return queryset.filter(usedin__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(usedin__isnull=True)
        else:
            return queryset
