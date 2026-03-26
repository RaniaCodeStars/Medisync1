from django.urls import path
from .views import clinic_signup_view,patient_signup_view,doctor_signup_view,role_choice,delete_account, login_view , logout_view, dashboard_patient, dashboard_medecin
from . import views
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.role_choice, name='role_choice'),
    path('delete/', delete_account, name='delete_account'),
    path('signup-medecin/', doctor_signup_view, name='doctor_signup'),
    path('waiting-validation/', TemplateView.as_view(template_name='accounts/waiting_validation.html' ), name='waiting_validation'),
    path('signup-patient/', patient_signup_view, name='patient_signup'),
     path('signup-clinic/', clinic_signup_view, name='clinic_signup'),
    #path('signup/medecin/success/', DoctorSignupSuccessView.as_view(), name='signup_doctor_success'),
     path('delete-account/', views.delete_account, name='delete_account'),
    # Patient
   # path('signup/patient/', PatientSignupView.as_view(), name='signup_patient'),
   # path('signup/patient/success/', PatientSignupSuccessView.as_view(), name='signup_patient_success'),
   # path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('dashboard-medecin/', dashboard_medecin, name='dashboard_medecin'),
    path('dashboard-patient/', dashboard_patient, name='dashboard_patient'),
   
    #path('dashboard-pharmacien/', dashboard_pharmacien, name='dashboard_pharmacien'),
]