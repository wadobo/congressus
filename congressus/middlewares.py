from django.utils.deprecation import MiddlewareMixin
from maintenancemode.models import Maintenance
from django.contrib.sites.models import Site


class FixMaintenanceDup(MiddlewareMixin):

    def process_request(self, request):
        site = Site.objects.get_current()

        while Maintenance.objects.filter(site=site).count() > 1:
            mm = Maintenance.objects.filter(site=site).order_by('-pk')[0]
            mm.delete()
