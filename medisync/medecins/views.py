from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from medecins.models import Doctor
from clinics.models import Clinic
from datetime import datetime, timedelta
from django.utils import timezone

def get_week_availability(doctor, start_week, end_week):
    """Récupère les disponibilités hebdomadaires et spécifiques pour un médecin"""
    availability_by_day = {
        'monday': [],
        'tuesday': [],
        'wednesday': [],
        'thursday': [],
        'friday': [],
        'saturday': [],
        'sunday': []
    }
    
    # Récupérer les disponibilités hebdomadaires
    for wa in doctor.weekly_availabilities.all().order_by('start_time'):
        availability_by_day[wa.day].append({
            'start_time': wa.start_time.strftime('%H:%M'),
            'end_time': wa.end_time.strftime('%H:%M'),
            'is_emergency': wa.is_emergency,
            'type': 'weekly'
        })
    
    # Récupérer les disponibilités spécifiques
    for sa in doctor.specific_availabilities.filter(
        date__range=[start_week, end_week],
        is_active=True
    ).order_by('start_time'):
        day_name = sa.date.strftime('%A').lower()
        availability_by_day[day_name].append({
            'start_time': sa.start_time.strftime('%H:%M'),
            'end_time': sa.end_time.strftime('%H:%M'),
            'is_emergency': False,
            'type': 'specific',
            'date': sa.date.strftime('%Y-%m-%d')
        })
    
    # Convertir en liste ordonnée pour le template
    week_availability = []
    for day, day_name in [('monday', 'Lundi'), ('tuesday', 'Mardi'), 
                         ('wednesday', 'Mercredi'), ('thursday', 'Jeudi'),
                         ('friday', 'Vendredi'), ('saturday', 'Samedi'),
                         ('sunday', 'Dimanche')]:
        week_availability.append({
            'day_name': day_name,
            'day_key': day,
            'availabilities': availability_by_day[day] or None
        })
    
    return week_availability

def doctor_list(request):
    """
    Affiche une liste de médecins et de cliniques en fonction des critères de recherche.
    """
    recherche = request.GET.get('recherche', '').strip()
    location = request.GET.get('location', '').strip()

    # Initialisation des résultats
    doctors = Doctor.objects.all()
    clinics = Clinic.objects.all()

    # Filtrage par recherche
    if recherche:
        doctors = doctors.filter(
            Q(nom__icontains=recherche) |
            Q(prenom__icontains=recherche) |
            Q(specialty__nom__icontains=recherche) |
            Q(institution__icontains=recherche)
        )
        clinics = clinics.filter(name__icontains=recherche)

    # Filtrage par localisation
    if location:
        doctors = doctors.filter(location__iexact=location)
        clinics = clinics.filter(location__iexact=location)

    # Calcul de la semaine courante
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())  # Début de semaine (lundi)
    end_week = start_week + timedelta(days=6)  # Fin de semaine (dimanche)

    # Ajout des disponibilités à chaque médecin
    for doctor in doctors:
        doctor.week_availability = get_week_availability(doctor, start_week, end_week)

    # Contexte pour le rendu
    context = {
        'doctors': doctors,  # On passe directement les objets Doctor
        'clinics': clinics
    }
    return render(request, 'medecins/doctor_list.html', context)

def doctors_api(request):
    """
    Renvoie une API JSON avec les informations des médecins et des cliniques.
    """
    doctors = Doctor.objects.select_related('specialty').all()
    clinics = Clinic.objects.all()

    data = {
        "doctors": [
            {
                "name": f"Dr. {doc.nom} {doc.prenom}",
                "specialty": doc.specialty.nom if doc.specialty else "Non spécifié",
                "institution": doc.institution,
                "location": doc.location,
                "latitude": doc.latitude,
                "longitude": doc.longitude,
                "experience": doc.experience
            }
            for doc in doctors
        ],
        "clinics": [
            {
                "name": clinic.name,
                "phone": clinic.phone,
                "location": clinic.location,
                "latitude": clinic.latitude,
                "longitude": clinic.longitude
            }
            for clinic in clinics
        ]
    }

    return JsonResponse(data, safe=False)

#------------------------------------------------------------------------------------------------------------------
# Parametre
#------------------------------------------------------------------------------------------------------------------

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Notification


@login_required
def medcin_settings(request):
    """
    Vue pour afficher la page des paramètres du patient.
    """
    medcin = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    
    context = {
        'doctor_name': f"{medcin.doctor_profile.nom} {medcin.doctor_profile.prenom}" if hasattr(medcin, 'doctor_profile') else medcin.username,
        'profile_picture': request.user.profile_picture.url if getattr(request.user, 'profile_picture', None) else None,
        'edit_profile_url': 'medecins:medcin_edit_profile',  # URL pour modifier le profil
        'unread_notification_count': unread_count,
        'appointments_history_url': 'appointments:medcin_appointment_history',  # URL pour l'historique des rendez-vous
    }
    return render(request, 'medecins/medcin_settings.html', context)


# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Doctor

@login_required
def toggle_notifications(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        medcin = Doctor.objects.get(user=request.user)
        enabled = request.POST.get('enabled') == 'true'
        medcin.notifications = enabled
        medcin.save()
        return JsonResponse({'status': 'success', 'enabled': enabled})
    return JsonResponse({'status': 'error'}, status=400)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Specialty
from .models import WILAYA_CHOICES

@login_required
def edit_profile(request):
    """
    Vue pour modifier le profil du patient.
    """
    doctor = request.user.doctor_profile
    user = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    specialties = Specialty.objects.all()
    
    if request.method == 'POST':
        doctor.nom = request.POST.get('nom')
        doctor.prenom = request.POST.get('prenom')
        doctor.compte_RIP = request.POST.get('compte_RIP')
        user.phone = request.POST.get('phone')
        user.date_of_birth = request.POST.get('date_of_birth') if request.POST.get('date_of_birth') else None
        
        # Gestion des champs numériques avec validation
        try:
            doctor.experience = int(request.POST.get('experience', 0))
        except (ValueError, TypeError):
            doctor.experience = 0
            
        try:
            doctor.default_duration = int(request.POST.get('default_duration', 30))
        except (ValueError, TypeError):
            doctor.default_duration = 30
            
        try:
            doctor.minimum_delay = int(request.POST.get('minimum_delay')) if request.POST.get('minimum_delay') else None
        except (ValueError, TypeError):
            doctor.minimum_delay = None
            
        try:
            doctor.maximum_delay = int(request.POST.get('maximum_delay')) if request.POST.get('maximum_delay') else None
        except (ValueError, TypeError):
            doctor.maximum_delay = None
            
        try:
            doctor.prix = float(request.POST.get('prix', 0))
        except (ValueError, TypeError):
            doctor.prix = 0.00
            
        doctor.accept_online_appointments = 'accept_online_appointments' in request.POST
        doctor.notifications = 'notifications' in request.POST
        doctor.location = request.POST.get('location')
        doctor.specialty_id = request.POST.get('specialty')
        doctor.institution = request.POST.get('institution')

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        try:
            user.save()
            doctor.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('medecins:medcin_settings')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue: {str(e)}")

    context = {
        'doctor': doctor,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'unread_notification_count': unread_count,
        'specialties': specialties,
        'wilaya_choices': WILAYA_CHOICES,
    }
    
    return render(request, 'medecins/medcin_edit_profile.html', context)