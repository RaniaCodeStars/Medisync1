from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

class ProfileInline(admin.StackedInline):  
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profils'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuration de l'interface admin pour le modèle User.
    """
    list_display = ('username', 'email', 'phone', 'get_role', 'is_staff', 'is_superuser')
    list_filter = ('profile__role',)  # ✅ Corrigé pour filtrer par role depuis Profile
    search_fields = ('username', 'email', 'phone')
    ordering = ('username',)
    inlines = [ProfileInline]  # ✅ Ajoute le profil à l'admin

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('phone',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Statut', {'fields': ('is_active',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'phone'),
        }),
    )

    def get_role(self, obj):
        return obj.profile.role  # ✅ Accéder au rôle depuis Profile
    get_role.admin_order_field = 'profile__role'
    get_role.short_description = 'Rôle'

admin.site.register(Profile)  # ✅ Optionnel si tu veux voir Profile séparément
