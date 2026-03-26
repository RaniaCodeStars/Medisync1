# medcin/urls.py
from django.urls import path
from . import views
from .views import doctors_api

app_name = 'medecins'

urlpatterns = [
    path('medecins/doctor_list/', views.doctor_list, name='doctor_list'),
    path('api/doctors/', doctors_api, name='doctors_api'),
    path('settings/', views.medcin_settings, name='medcin_settings'),
    path('toggle-notifications/', views.toggle_notifications, name='toggle_notifications'),
    path('edit-profile/', views.edit_profile, name='medcin_edit_profile'),
]

