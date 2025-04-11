from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AdminNotification

User = get_user_model()

@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    if created and instance.is_staff:
        from .models import AdminProfile
        AdminProfile.objects.create(user=instance)

def send_admin_notification(admin, message, notification_type, metadata=None):
    AdminNotification.objects.create(
        admin=admin,
        message=message,
        notification_type=notification_type,
        metadata=metadata or {}
    )