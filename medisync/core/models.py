from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()



class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
# Create your models here.
