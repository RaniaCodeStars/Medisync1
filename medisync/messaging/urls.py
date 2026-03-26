from django.urls import path
from .views import chat_view
from . import views


app_name = "messaging"


urlpatterns = [
    path('', chat_view, name='chat_list'),
    path('<str:username>/', chat_view, name='chat'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
]
