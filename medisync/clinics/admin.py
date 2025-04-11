from django.contrib import admin
from .models import Clinic, Review

from django.contrib import admin
from .models import Clinic

class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'location', 'display_horaires')  # Affichage dans la liste des cliniques
    readonly_fields = ('horaires',)  # Empêche la modification du champ "horaires"

    def display_horaires(self, obj):
        return obj.horaires if obj.horaires else "Non défini"
    display_horaires.short_description = "Horaires"

    def get_readonly_fields(self, request, obj=None):
        """
        Rend 'horaires' en lecture seule lors de l'édition, mais permet de le modifier à la création.
        """
        if obj:  # Si l'objet existe déjà (mode édition), rendre "horaires" en lecture seule
            return self.readonly_fields + ('horaires',)
        return self.readonly_fields

admin.site.register(Clinic ,ClinicAdmin)










from django.contrib import admin
from .models import Clinic, ClinicDoctor

class ClinicDoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'speciality', 'clinic')  # Colonnes affichées dans l'admin
    search_fields = ('name', 'speciality', 'clinic__name')  # Ajoute une barre de recherche
    list_filter = ('clinic', 'speciality')  # Ajoute des filtres par clinique et spécialité

admin.site.register(ClinicDoctor, ClinicDoctorAdmin)  # Enregistre le modèle













@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour Review.
    """
    list_display = ('clinic', 'rating', 'comment')  # Colonnes principales affichées
    search_fields = ('clinic__name', 'comment')  # Recherche par nom de clinique ou commentaire
    list_filter = ('rating', 'clinic')  # Filtrage par note et clinique











from django.contrib import admin
from .models import DemandeDeParticipation

@admin.register(DemandeDeParticipation)
class DemandeDeParticipationAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'speciality', 'clinic', 'status', 'request_date')
    list_filter = ('status', 'clinic')
    search_fields = ('doctor_name', 'speciality', 'clinic__name')






# clinics/admin.py
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'clinic', 'speciality', 'date', 'time_slot', 'status')
    list_filter = ('status', 'clinic', 'speciality')
    search_fields = ('patient__email', 'patient__first_name', 'patient__last_name')