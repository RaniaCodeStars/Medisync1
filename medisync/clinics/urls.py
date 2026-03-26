from django.urls import path, include
from . import views

app_name = 'clinics'

urlpatterns = [
    path('core/', views.home, name='home'),

    path('', views.clinic_profile, name='clinic_profile'),#-
    path('edit/', views.edit_clinic, name='clinic_edit'),#-
    path('dashboard/', views.clinic_dashboard, name='clinic_dashboard'),#-
    path('edit_horaires/', views.edit_horaires, name='edit_horaires'),#-
    path('horaires/save/', views.save_horaires, name='save_horaires'),
    path('manage/doctors/', views.manage_doctors, name='manage_doctors'),
    path('doctor/rendezvous/<int:doctor_id>/', views.doctor_rendezvous, name='doctor_rendezvous'),


    path('manage/add_doctor/', views.add_doctor_to_clinic, name='add_doctor'),
    path('doctor/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),
    path('doctor/<int:doctor_id>/edit/', views.edit_doctor, name='edit_doctor'),

    path('ajouter-horaire/<int:doctor_id>/', views.ajouter_horaire, name='ajouter_horaire'),#pour medcin
    path('modifier-horaire/<int:doctor_id>/<int:horaire_id>/', views.modifier_horaire, name='modifier_horaire'),

    # Reviews (tu peux garder l'id ici si plusieurs users peuvent commenter une clinique)
    path('reviews/', views.clinic_reviews, name='clinic_reviews'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('review/<int:review_id>/reply/', views.reply_review, name='reply_review'),
    path('planning-clinique/', views.afficher_horaires, name='afficher_horaires'),

    path('settings/', views.clinic_settings, name='clinic_settings'),
    path('add-clinic-doctor/', views.create_clinic_doctor, name='add_clinic_doctor'),#hadi ?
    path('confirm-doctor/', views.confirm_doctor, name='confirm_doctor'),#supprimer et confirmer un doctieru
    
    path('gerer-demande/<int:demande_id>/', views.gerer_demande, name='confirmer_demande_docteur'),
    path('centre-aide/', views.help_center, name='help_center'),
    path('modal-info/', views.clinic_modal_info, name='clinic_modal_info'),
    
    path('confirm-demande/<int:demande_id>/', views.confirm_demande, name='envoyez-rendez-vous'), #envoyer rendez vous(demande) 
    path('mes-demandes/', views.mes_demandes, name='mes_demandes'),
    
    path('demande/<int:demande_id>/confirmer/', views.confirmer_demande, name='confirmer_demande'),#confimer un rendez vous 
    path('demande/<int:demande_id>/supprimer/', views.supprimer_demande, name='supprimer_demande'),#supprimer un rendez vous 
    
    path('rendez-vous/envoyer/', views.envoyer_rendez_vous, name='envoyez-rendez-vous'),#demande de rendez vous 
    path('rendez-vous/ajouter/', views.ajouter_rendez_vous, name='ajouter_rendez_vous'),
    path('rendez-vous/confirmation/', views.confirmation_rendez_vous, name='confirmation_rendez_vous'),
    # views.py est déjà importé
    path('rendez-vous/<int:rdv_id>/modifier/', views.modifier_rendez_vous, name='modifier_rendez_vous'),
    path('rendez-vous/<int:rdv_id>/supprimer/', views.supprimer_rendez_vous, name='supprimer_rendez_vous'),
    path('review/<slug:clinic_slug>/', views.add_review, name='add_review'),


    path('admin/', include(('administrators.urls', 'administrators'), namespace='administrators')),

]
