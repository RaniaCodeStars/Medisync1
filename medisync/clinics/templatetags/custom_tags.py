# clinics/templatetags/custom_tags.py
from django import template
from datetime import time, timedelta, datetime

register = template.Library()

@register.filter
def heure_range(_=None):
    heures = []
    h = datetime.strptime("00:00", "%H:%M")
    for i in range(0, 24):
        heures.append((h + timedelta(hours=i)).time())
    return heures
