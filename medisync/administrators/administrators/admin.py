from django.contrib import admin
from .models import AdminProfile, AdminNotification, AdminActivityLog

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'special_access', 'last_activity')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('last_activity',)

@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('admin', 'message_preview', 'notification_type', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type')
    search_fields = ('message', 'admin__email')
    readonly_fields = ('created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_preview', 'ip_address', 'timestamp')
    search_fields = ('action', 'admin__email')
    readonly_fields = ('timestamp', 'user_agent')
    list_filter = ('timestamp',)
    
    def action_preview(self, obj):
        return obj.action[:50] + '...' if len(obj.action) > 50 else obj.action
    action_preview.short_description = 'Action'