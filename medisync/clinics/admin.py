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
from .models import Clinic, ClinicDoctor, RendezVous

# Enregistrer le modèle ClinicDoctor dans l'admin
class ClinicDoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'speciality', 'clinic', 'get_rendezvous')
    search_fields = ('name', 'speciality', 'clinic__name')
    list_filter = ('clinic', 'speciality')

    def get_rendezvous(self, obj):
        return f"{obj.rendezvous.count()} rendez-vous" if obj.rendezvous.exists() else "Aucun rendez-vous"
    get_rendezvous.short_description = 'Rendez-vous'

admin.site.register(ClinicDoctor, ClinicDoctorAdmin)









from django.contrib import admin
from .models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'clinic', 'rating', 'created_at', 'reply')  # Champs à afficher dans la liste
    list_filter = ('clinic', 'rating')  # Ajouter des filtres
    search_fields = ('user__email', 'clinic__name', 'comment')  # Rechercher par email de l'utilisateur, nom de la clinique, ou commentaire
    date_hierarchy = 'created_at'  # Trier les avis par date

admin.site.register(Review, ReviewAdmin)  # Enregistrer le modèle avec sa configuration








from django.contrib import admin
from .models import DemandeDeParticipation

@admin.register(DemandeDeParticipation)
class DemandeDeParticipationAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'speciality', 'clinic', 'status', 'request_date')
    list_filter = ('status', 'clinic')
    search_fields = ('doctor_name', 'speciality', 'clinic__name')




from django.contrib import admin
from .models import HoraireClinic

@admin.register(HoraireClinic)
class HoraireClinicAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'jour', 'heure_ouverture', 'heure_fermeture', 'est_ferme', 'date')
    list_filter = ('clinic', 'jour', 'est_ferme')
    search_fields = ('clinic__name', 'jour')




# admin.py
from django.contrib import admin
from .models import HoraireTravail
from .forms import HoraireTravailForm

@admin.register(HoraireTravail)
class HoraireTravailAdmin(admin.ModelAdmin):
    form = HoraireTravailForm
    list_display = ('doctor', 'jour', 'heure_debut', 'heure_fin')
    list_filter = ('jour', 'doctor')
    search_fields = ('doctor__name',)










































from django.contrib import admin
from .models import DemandeRendezVous, RendezVous

@admin.register(DemandeRendezVous)
class DemandeRendezVousAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'nom', 'clinic', 'get_speciality', 'jour', 'heure', 'status')
    list_filter = ('clinic', 'speciality', 'jour', 'status')
    search_fields = ('nom', 'doctor__name', 'clinic__name', 'speciality__nom')

    def get_speciality(self, obj):
        return obj.speciality.nom if obj.speciality else "-"
    get_speciality.short_description = "Spécialité"



from django.contrib import admin
from .models import RendezVous
# Enregistrer le modèle RendezVous dans l'admin
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'nom', 'clinic', 'get_speciality', 'jour', 'heure', 'status')
    list_filter = ('clinic', 'speciality', 'jour', 'status')
    search_fields = ('nom', 'doctor__name', 'clinic__name', 'speciality__nom')

    def get_speciality(self, obj):
        return obj.speciality.nom if obj.speciality else "-"
    get_speciality.short_description = "Spécialité"

admin.site.register(RendezVous, RendezVousAdmin)









