from django.urls import path
from . import views

app_name = 'administrators'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Gestion des médecins
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/approve/<int:doctor_id>/', views.approve_doctor, name='approve_doctor'),
    path('doctors/reject/<int:doctor_id>/', views.reject_doctor, name='reject_doctor'),
    
    # Gestion des patients
    path('patients/', views.patient_list, name='patient_list'),
    
    # Gestion des rendez-vous
    path('appointments/', views.appointment_list, name='appointment_list'),
    
    # API Endpoints
    path('api/appointments-stats/', views.api_appointments_stats, name='appointments_stats'),
    path('api/specialties-stats/', views.api_specialties_stats, name='specialties_stats'),
]