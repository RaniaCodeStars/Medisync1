from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Administration des notifications.
    """
    list_display = ('user', 'message', 'sent_at')
    list_filter = ('sent_at',)
    search_fields = ('user__email', 'message')
    ordering = ('-sent_at',)
