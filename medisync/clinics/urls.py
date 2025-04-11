from django.urls import path
from . import views
from .views import clinic_profile,edit_clinic,clinic_dashboard,edit_horaires,manage_doctors,add_doctor_to_clinic,delete_doctor,edit_doctor,clinic_reviews, add_review, delete_review, reply_review,clinic_settings,create_clinic_doctor,confirm_doctor,gerer_demande
from django.urls import path

urlpatterns = [
    path('<int:clinic_id>/', clinic_profile, name='clinic_profile'),
    path('<int:clinic_id>/edit/', edit_clinic, name='clinic_edit'),
    path('<int:clinic_id>/dashboard/', views.clinic_dashboard, name='clinic_dashboard'),
    path('<int:clinic_id>/edit_horaires/', edit_horaires, name='edit_horaires'),
    path('manage/<int:clinic_id>/doctors/', manage_doctors, name='manage_doctors'),
    path('manage/<int:clinic_id>/add_doctor/', views.add_doctor_to_clinic, name='add_doctor'),
    path('doctor/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),
    path('doctor/<int:doctor_id>/edit/', views.edit_doctor, name='edit_doctor'),
    path('<int:clinic_id>/reviews/', clinic_reviews, name='clinic_reviews'),
    path('clinic/<int:clinic_id>/add_review/', add_review, name='add_review'),
    path('review/<int:review_id>/delete/', delete_review, name='delete_review'),
    path('review/<int:review_id>/reply/', reply_review, name='reply_review'),
    path('<int:clinic_id>/settings/', clinic_settings, name='clinic_settings'),
    path('clinic/<int:clinic_id>/add-doctor/', create_clinic_doctor, name='add_clinic_doctor'),
    path('clinic/confirm-doctor/<int:clinic_id>/', confirm_doctor, name='confirm_doctor'),
    path('confirm-doctor/<int:clinic_id>/', confirm_doctor, name='confirm_doctor'),
    path('gerer-demande/<int:clinic_id>/<int:demande_id>/', gerer_demande, name='confirmer_demande'),
    path('centre-aide/', views.help_center, name='help_center'),
    path('prendre_rendez_vous/<int:clinic_id>/', views.prendre_rendez_vous, name='prendre_rdv'),
    path('annuler_rendez_vous/<int:appointment_id>/', views.annuler_rendez_vous, name='annuler_rdv'),
    path('rendez-vous/succes/', views.rendez_vous_succes, name='rendez_vous_succes'),



]









