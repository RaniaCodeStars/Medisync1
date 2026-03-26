from django.contrib import admin
from .models import AdminProfile,NotificationGenerale,  AdminActivityLog ,ReportedIssue,IssueCategory,IssueUpdate

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'special_access', 'last_activity')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('last_activity',)

@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_preview', 'ip_address', 'timestamp')
    search_fields = ('action', 'admin__email')
    readonly_fields = ('timestamp', 'user_agent')
    list_filter = ('timestamp',)
    
    def action_preview(self, obj):
        return obj.action[:50] + '...' if len(obj.action) > 50 else obj.action
    action_preview.short_description = 'Action'



class IssueUpdateInline(admin.TabularInline):
    model = IssueUpdate
    extra = 0
    readonly_fields = ('author', 'created_at')

@admin.register(ReportedIssue)
class ReportedIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'reporter', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description')
    inlines = [IssueUpdateInline]
    autocomplete_fields = ('reporter', 'assigned_to', 'related_appointment')

from django.contrib import admin
from .models import NotificationGenerale

@admin.register(NotificationGenerale)
class NotificationGeneraleAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'sender__username', 'recipient__username')
    ordering = ('-created_at',)
