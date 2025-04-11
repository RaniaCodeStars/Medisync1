"""
URL configuration for medisync project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# medisync/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static


def home_view(request):  
    return render(request, "core/home.html")  # Chemin correct du template

urlpatterns = [
    path('admin/', admin.site.urls),  # Interface d'administration Django
    path('accounts/', include('accounts.urls')),  # URLs de l'application accounts
    path('medecins/', include('medecins.urls')),
    path('clinic/', include('clinics.urls')), 
    path('', include('core.urls')),  # URLs de l'application core (pour la page d'accueil, etc.)
    path('appointments/', include('appointments.urls')),
    # path('api/', include('api.urls')),  # Inclure les URLs de l'API

]
if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

