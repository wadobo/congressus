from django import template


register = template.Library()


@register.simple_tag
def tickets_today(w, date):
    return w.tickets_today(date)

@register.simple_tag
def sold_today(w, date):
    return w.sold_today(date)

@register.simple_tag
def sold_today_cash(w, date):
    return w.sold_today_cash(date)

@register.simple_tag
def sold_today_card(w, date):
    return w.sold_today_card(date)

@register.simple_tag
def session_price(w, session):
    if not w:
        return session.price
    return w.get_price(session)
