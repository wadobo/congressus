from django.contrib import admin
from django.utils.translation import gettext_lazy as _


try:
    import theme
except Exception:
    admin.site.site_title = _('Congressus admin')
    admin.site.site_header = _('Congressus admin')
