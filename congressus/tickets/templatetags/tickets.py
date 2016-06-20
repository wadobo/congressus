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

    if session.is_seat_holded(layout, row, col):
        return 'seat-H'

    if session.is_seat_available(layout, row, col):
        return 'seat-L'

    return 'seat-R'


@register.simple_tag(takes_context=True)
def scene_span(context, map):
    if 'scenedraw' in context:
        return ''

    context.dicts[0]['scenedraw'] = True
    rows = (map.scene_bottom - map.scene_top) + 1
    cols = (map.scene_right - map.scene_left) + 1

    html = '<td class="scene" rowspan="%s" colspan="%s"> %s </td>' % (rows, cols, _('scene'))

    return mark_safe(html)
