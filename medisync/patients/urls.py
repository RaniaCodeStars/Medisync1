# patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    #path('book/<int:provider_id>/', views.book_appointment, name='book_appointment'),
    # Vous pouvez ajouter d'autres URLs ici au besoin
    path('dashboard/', views.patient_dashboard, name='dashboard'),
    path('documents/', views.patient_documents, name='patient_documents'),
    path('documents/delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('documents/download/<int:document_id>/', views.download_document, name='download_document'),
    path('settings/', views.patient_settings, name='patient_settings'),  # Paramètres du patient
    path('edit-profile/', views.edit_profile, name='patient_edit_profile'),
    path('notifications/', views.patient_notification_list, name='patient_notification_list'),  # Nouvelle route
    path('toggle-notifications/', views.toggle_notifications, name='toggle_notifications'),
    path('notifications/mark_as_read/<int:notification_id>/', 
         views.mark_notification_as_read, 
         name='patient_mark_notification_as_read'),
    path('notifications/delete/<int:notification_id>/', 
         views.delete_notification, 
         name='patient_delete_notification'),
    path('notifications/mark_all_as_read/', 
         views.mark_all_notifications_as_read, 
         name='patient_mark_all_notifications_as_read'),
    path('notifications/delete_all/', 
         views.delete_all_notifications, 
         name='patient_delete_all_notifications'),
    
]