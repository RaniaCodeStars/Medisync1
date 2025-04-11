# medcin/urls.py
from django.urls import path
from . import views
from .views import doctors_api
urlpatterns = [
    path('medecins/doctor_list/', views.doctor_list, name='doctor_list'),
    path('api/doctors/', doctors_api, name='doctors_api'),
]

