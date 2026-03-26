from .models import NotificationGenerale

def base_context(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': NotificationGenerale.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        }
    return {}