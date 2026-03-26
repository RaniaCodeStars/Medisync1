from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    # path('api/get-available-dates-v2/<int:doctor_id>/', views.get_available_dates_api_v2, name='get_available_dates_api_v2'),
    path('api/get-available-times/', views.get_available_times_api, name='get_available_times_api'),  # Ajoutez ceci
    path('api/get-availabilities/<int:doctor_id>/', views.get_availabilities_api, name='get_availabilities_api'),
    path('api/get-consultation-reasons/<int:doctor_id>/', views.get_consultation_reasons, name='get_consultation_reasons'),
    #path('api/get-weekly-available-dates/<int:doctor_id>/', views.get_weekly_available_dates_api, name='get_weekly_available_dates_api'),
    path('api/get-combined-available-dates/<int:doctor_id>/', views.get_combined_available_dates_api, name='get_combined_available_dates'),
    path("confirm-appointment/", views.confirm_appointment, name="confirm_appointment"),
    path("confirmation/<int:appointment_id>/", views.confirmation_page, name="confirmation_page"),
    path('api/get-doctor-info/<int:doctor_id>/', views.get_doctor_info, name='get_doctor_info'),

    #lien RV patient---------------------------------------------------------------------------------------------------------------------
    path('my-appointments/', views.patient_appointments, name='patient_appointments'),
    path('my-teleconsultations/', views.patient_teleconsultations, name='patient_teleconsultations'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('patient-urgent-appointments/', views.patient_urgent_appointments, name='patient_urgent_appointments'),
    path('patient-history/', views.patient_appointment_history, name='patient_appointment_history'),  # Historique des rendez-vous
    
    
    #lien RV doctor---------------------------------------------------------------------------------------------------------------------
    path('doctor-appointments/', views.medcin_appointments, name='medcin_appointments'),
    path('doctor-appointments/<int:appointment_id>/', views.doctor_appointment_detail, name='doctor_appointment_detail'),
    path('doctor-teleconsultations/', views.medcin_teleconsultations, name='medcin_teleconsultations'),
    path('doctor-appointments/<int:appointment_id>/modify/', views.modify_appointment, name='modify_appointment'),
    path('availability/manage/', views.manage_availability, name='manage_availability'),
    path('availability/weekly/<int:availability_id>/edit/', views.edit_weekly_availability, name='edit_weekly_availability'),
    path('availability/weekly/delete/<int:availability_id>/', views.delete_weekly_availability, name='delete_weekly_availability'),
    path('availability/emergency/delete/<int:availability_id>/', views.delete_emergency_availability, name='delete_emergency_availability'),
    path('availability/specific/<int:availability_id>/edit/', views.edit_specific_availability, name='edit_specific_availability'),
    path('availability/specific/<int:availability_id>/delete/', views.delete_specific_availability, name='delete_specific_availability'),
    path('consultation-reasons/', views.manage_consultation_reasons, name='manage_consultation_reasons'),
    path('consultation-reasons/<int:reason_id>/edit/', views.edit_consultation_reason, name='edit_consultation_reason'),
    path('consultation-reasons/<int:reason_id>/delete/', views.delete_consultation_reason, name='delete_consultation_reason'),
    path('urgent-appointments/', views.medcin_urgent_appointments, name='medcin_urgent_appointments'),
    path('doctor-history/', views.doctor_appointment_history, name='medcin_appointment_history'),
    path('medecin/notifications/', views.doctor_notifications, name='doctor_notifications'),
    path('medecin/notifications/marquer-lue/<int:notification_id>/', views.doctor_mark_notification_as_read, name='doctor_mark_notification_as_read'),
    path('medecin/notifications/supprimer/<int:notification_id>/', views.doctor_delete_notification, name='doctor_delete_notification'),
    path('medecin/notifications/marquer-tout-lu/', views.doctor_mark_all_notifications_as_read, name='doctor_mark_all_notifications_as_read'),
    path('medecin/notifications/supprimer-tout/', views.doctor_delete_all_notifications, name='doctor_delete_all_notifications'),
]

