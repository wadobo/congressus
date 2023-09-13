from django.contrib import admin

from .models import Dashboard
from .models import ConfigChart


@admin.register(ConfigChart)
class ConfigChartAdmin(admin.ModelAdmin):
    list_display = ("type", "timestep", "max_steps")


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ("event", "num_cols", "name")
    filter_horizontal = ("charts",)
    prepopulated_fields = {"slug": ["name"]}
