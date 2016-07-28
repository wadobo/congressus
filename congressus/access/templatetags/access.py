from django import template


register = template.Library()


@register.simple_tag
def checked_today(a, date):
    return a.checked_today(date)


@register.simple_tag
def checked_today_ok(a, date):
    return a.checked_today(date, status='ok')


@register.simple_tag
def checked_today_wrong(a, date):
    return a.checked_today(date, status='wrong')


@register.simple_tag
def checked_today_used(a, date):
    return a.checked_today(date, status='used')


@register.simple_tag
def checked_today_maybe(a, date):
    return a.checked_today(date, status='maybe')
