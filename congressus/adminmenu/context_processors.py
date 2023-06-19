from django.urls import reverse
from django.utils.translation import gettext as _


def links(request):
    u = request.user
    ctx = {}
    if not u.is_authenticated or not u.is_superuser:
        return ctx

    ctx['menu_links'] = [
        {'label': _('admin'), 'url': reverse('admin:index')},
    ]
    return ctx
