from django import template


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
