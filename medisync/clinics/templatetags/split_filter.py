from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    if value is None:
        return []
    return value.split(delimiter)
