from django import template
import json

register = template.Library()

@register.filter(name='tojson')
def tojson(value):
    return json.dumps(value)