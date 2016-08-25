import re

from django import template
from django.utils.translation import ugettext as _
from django.utils.html import mark_safe


register = template.Library()


@register.simple_tag
def ticket_seat_class(session, layout, seat, row, col):
    row = str(row)
    col = str(col)

    if seat == 'R':
        return 'seat-R'
    elif seat == '_':
        return 'seat-_'

    holded_type = session.is_seat_holded(layout, row, col)
    if holded_type:
        return 'seat-' + re.sub('[CP]', 'H', holded_type)

    if session.is_seat_available(layout, row, col):
        return 'seat-L'

    return 'seat-R'


@register.simple_tag(takes_context=True)
def scene_span(context, session, map):
    flag = 'scenedraw-%s' % session.id
    if flag in context:
        return ''

    context.dicts[0][flag] = True
    rows = (map.scene_bottom - map.scene_top) + 1
    cols = (map.scene_right - map.scene_left) + 1

    html = '<td class="scene" rowspan="%s" colspan="%s"> %s </td>' % (rows, cols, _('scene'))

    return mark_safe(html)


@register.simple_tag
def key(data, key, prefix="", default=''):
    k = key
    if prefix:
        k = prefix + str(key)
    return data.get(k, default)
