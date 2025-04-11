from django import template

register = template.Library()

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])




from django import template

register = template.Library()

@register.filter
def get_item(list, index):
    try:
        return list[index]
    except:
        return None