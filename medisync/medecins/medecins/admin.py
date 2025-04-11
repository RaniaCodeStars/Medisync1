from django.contrib import admin
from .models import Specialty, Doctor  # Supprimez `Clinic`
from clinics.models import Clinic  # Importez `Clinic` depuis l'app clinic
from accounts.models import User


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour Specialty.
    """
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour Doctor.
    """
    list_display = ('user', 'nom', 'prenom', 'specialty', 'experience', 'location',
                     'accept_online_appointments', 'compte_RIP', 'prix')  # Ajout de la localisation
    search_fields = ('nom', 'prenom', 'specialty__nom', 'user__email', 'user__username')  # Utilisation des champs 'email' et 'username'
    list_filter = ('specialty', 'location', 'accept_online_appointments')  # Filtrage par localisation ajouté
    list_editable = ('accept_online_appointments',)


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtrer les utilisateurs dans le champ user pour afficher seulement ceux avec is_doctor=True.
        """
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(profile__role='MEDECIN')  # Filtrage basé sur le rôle dans Profile
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

