


from django import template
import json
from datetime import time

register = template.Library()

@register.filter
def json_serialize(value):
    def time_serializer(obj):
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        raise TypeError(f"Type {type(obj)} not serializable")
    
    return json.dumps(list(value.values('jour', 'heure_debut', 'heure_fin')), default=time_serializer)