# patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    #path('book/<int:provider_id>/', views.book_appointment, name='book_appointment'),
    # Vous pouvez ajouter d'autres URLs ici au besoin
]