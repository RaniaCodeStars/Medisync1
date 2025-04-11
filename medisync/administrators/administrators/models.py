from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    special_access = models.BooleanField(default=False)
    dashboard_config = models.JSONField(default=dict)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin Profile - {self.user.email}"

class AdminNotification(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

class AdminActivityLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']