from django.contrib import admin
from .models import Patient, MedicalHistory, PatientDocument
from accounts.models import User


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour Patient.
    """
    list_display = ('user', 'nom', 'prenom','sex', 'blood_group', 'height', 'weight', 'notifications')
    search_fields = ('nom', 'prenom', 'user__email', 'user__first_name', 'user__last_name')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtrer le champ User pour afficher uniquement les utilisateurs ayant le rôle PATIENT.
        """
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(profile__role='PATIENT').order_by('first_name', 'last_name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour MedicalHistory.
    """
    list_display = ('patient', 'condition', 'date')
    list_filter = ('date', 'condition')
    search_fields = ('patient__user__email', 'patient__nom', 'patient__prenom', 'condition')



@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'description', 'uploaded_at')  # Colonnes affichées dans la liste
    search_fields = ('patient__username', 'description')  # Recherche par patient ou description
    list_filter = ('uploaded_at',)  # Filtre sur la date d'ajout
    date_hierarchy = 'uploaded_at'  # Ajoute une barre de navigation par date
