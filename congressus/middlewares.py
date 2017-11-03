from django.utils import deprecation
from django import VERSION as DJANGO_VERSION
from maintenancemode.models import Maintenance
from django.contrib.sites.models import Site


class FixMaintenanceDup(deprecation.MiddlewareMixin if DJANGO_VERSION >= (1, 10, 0) else object):

    def process_request(self, request):
        site = Site.objects.get_current()

        while Maintenance.objects.filter(site=site).count() > 1:
            mm = Maintenance.objects.filter(site=site).order_by('-pk')[0]
            mm.delete()
