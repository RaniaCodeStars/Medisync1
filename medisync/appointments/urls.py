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
    #lien RV patient---------------------------------------------------------------------------------------------------------------------
    path('my-appointments/', views.patient_appointments, name='patient_appointments'),
    path('my-teleconsultations/', views.patient_teleconsultations, name='patient_teleconsultations'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    
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
]

