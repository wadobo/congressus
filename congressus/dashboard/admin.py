from django.contrib import admin

from .models import Dashboard
from .models import ConfigChart


class ConfigChartAdmin(admin.ModelAdmin):
    list_display = ('type', 'timestep',  'max_steps')


class DashboardAdmin(admin.ModelAdmin):
    list_display = ('event', 'num_cols', 'name')
    filter_horizontal = ('charts',)


admin.site.register(ConfigChart, ConfigChartAdmin)
admin.site.register(Dashboard, DashboardAdmin)
