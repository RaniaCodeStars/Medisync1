from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import  (ClinicListView,ArchiveDoctorView,ClinicCreateView,ClinicDeleteView,ClinicForm,ClinicUpdateView, ClinicDetailView,PatientListView ,PatientCreateView ,PatientDetailView ,PatientUpdateView,PatientDeleteView ,PatientStatsView,PatientExportView
      ,PatientImportView,ApproveDoctorView,ClinicStatsView,RejectDoctorView,DoctorCreateView,DoctorListView,AdminAppointmentsView,DoctorDetailView,DoctorStatsView,DoctorUpdateView,PendingDoctorsView
      )
from django.contrib.admin.views.decorators import staff_member_required
app_name = 'administrators'

urlpatterns = [
    
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    #gestion des specialty
    path('specialites/', views.gerer_specialites, name='gerer_specialites'),
   path('specialites/supprimer/<int:pk>/', views.supprimer_specialite, name='supprimer_specialite'),
    #gestion patients
    path('admin/patients/', PatientListView, name='admin_patients_list'),
    path('admin/patients/create/', PatientCreateView, name='admin_patient_create'),
    path('admin/patients/<int:pk>/', PatientDetailView.as_view(), name='admin_patient_detail'),
    path('patients/<int:patient_id>/update/', staff_member_required(PatientUpdateView), name='patient_update'),
    path('patients/<int:pk>/delete/', staff_member_required(PatientDeleteView.as_view()), name='patient_delete'), path('admin/patients/stats/', PatientStatsView.as_view(), name='admin_patients_stats'),
    path('patients/export/', PatientExportView.as_view(), name='admin_patient_export'),
    path('patients/import/', PatientImportView.as_view(), name='admin_patient_import'),
    
    #gestion medecins
    path('doctorlist/', DoctorListView.as_view(), name='doctor_list'),
    path('doctorAdd/',DoctorCreateView,name='doctor_add'),
    path('doctorlistValidation/',PendingDoctorsView.as_view(), name='doctor_validation'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor_detail'),
    path('<int:pk>/edit/', DoctorUpdateView.as_view(), name='doctor_update'),
    path('doctors/<int:pk>/archive/', ArchiveDoctorView.as_view(), name='archive_doctor'),
    
    path('doctors/<int:pk>/approve/', ApproveDoctorView.as_view(), name='approve_doctor'),
    path('doctors/<int:pk>/reject/', RejectDoctorView.as_view(), name='reject_doctor'),
    
    path('admin/doctor-stats/', DoctorStatsView.as_view(), name='doctor_stats'),
    #gestion clinic
     path('clinics/pending/', views.pending_clinics, name='pending_clinics'),
    path('clinics/<int:clinic_id>/approve/', views.approve_clinic, name='approve_clinic'),
    path('clinics/<int:clinic_id>/reject/', views.reject_clinic, name='reject_clinic'),
     path('clinics/', ClinicListView.as_view(), name='clinic-list'),
    path('clinics/<int:pk>/', ClinicDetailView.as_view(), name='clinic_detail'),
    path('clinics/add/', ClinicCreateView.as_view(), name='clinic_create'),
    path('clinic-stats/', ClinicStatsView.as_view(), name='clinic_stats'),
    path('clinics/<int:pk>/update/', ClinicUpdateView.as_view(), name='clinic_update'),
    path('clinics/<int:pk>/delete/', ClinicDeleteView.as_view(), name='clinic_delete'),
    #rendez-vous
    path('admin/appointments/', AdminAppointmentsView.as_view(), name='appointment_list'),

#notifications
    path('notification/', views.notification_list_view, name='notification_list'),
    path('notification/<int:notification_id>/', views.notification_detail_view, name='notification_detail'),
    path('notification/mark-all-read/', views.mark_all_as_read_view, name='mark_all_read'),
   ]
if settings.DEBUG:urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)