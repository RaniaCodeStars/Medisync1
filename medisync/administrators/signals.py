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
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import Profile  # ou selon ton app

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages
from django.shortcuts import redirect

@receiver(user_logged_in)
def check_doctor_approval(sender, request, user, **kwargs):
    if hasattr(user, 'doctor_profile'):
        if user.doctor_profile.status != 'approved':
            messages.error(request, "Votre compte médecin n'a pas encore été approuvé par l'administrateur.")
            # Déconnecter l'utilisateur
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')