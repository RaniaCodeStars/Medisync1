from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    STATUS_CHOICES = (
        ('unread', 'Non lue'),
        ('read', 'Lue'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='unread',  # Par défaut, la notification est "non lue"
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification pour {self.user.username} : {self.message[:50]}"
