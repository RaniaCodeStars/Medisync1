from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import WeeklyAvailability, SpecificAvailability, Appointment, ConsultationReason
from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import WeeklyAvailability, SpecificAvailability, Appointment, ConsultationReason
from .forms import AppointmentForm  # ✅ Importer le formulaire

@admin.register(ConsultationReason)
class ConsultationReasonAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour ConsultationReason.
    """
    list_display = ('doctor', 'name', 'duration' ,'prix')
    search_fields = ('name',)
    list_filter = ('duration', 'doctor')

@admin.register(WeeklyAvailability)
class WeeklyAvailabilityAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour WeeklyAvailability.
    """
    list_display = ('doctor', 'day', 'start_time', 'end_time', 'is_emergency')
    list_filter = ('doctor', 'day')
    search_fields = ('doctor__user__email', 'doctor__user__username')

@admin.register(SpecificAvailability)
class SpecificAvailabilityAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour SpecificAvailability.
    """
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_active')
    list_filter = ('doctor', 'date', 'is_active')
    search_fields = ('doctor__user__email', 'doctor__user__username')




@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour Appointment.
    """
    form = AppointmentForm  # ✅ Associer le formulaire personnalisé
    list_display = ('doctor', 'patient', 'date', 'time', 'consultation_reason', 'status', 'payment_status', 'is_online', 'prix', 'online_link', 'is_emergency','emergency_reason' )
    list_filter = ('status', 'doctor', 'date', 'consultation_reason', 'payment_status')
    search_fields = ('doctor__user__email', 'patient__email', 'consultation_reason__name')
    actions = ['confirm_appointments', 'cancel_appointments']

    def save_model(self, request, obj, form, change):
        """
        Applique les validations avant de sauvegarder un rendez-vous.
        """
        try:
            obj.clean()  # Exécuter la validation définie dans le modèle
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Erreur : {e}")

    def confirm_appointments(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, "Les rendez-vous sélectionnés ont été confirmés.")

    confirm_appointments.short_description = "Confirmer les rendez-vous sélectionnés"

    def cancel_appointments(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, "Les rendez-vous sélectionnés ont été annulés.")

    cancel_appointments.short_description = "Annuler les rendez-vous sélectionnés"
