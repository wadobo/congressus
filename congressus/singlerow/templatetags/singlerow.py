from django import template


register = template.Library()


@register.filter('startswith')
def startswith(text, start):
    try:
        return text.startswith(start)
    except:
        return False
