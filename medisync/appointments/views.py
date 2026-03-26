from django.shortcuts import render, get_object_or_404
from medecins.models import Doctor
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta, time
from appointments.models import Appointment, SpecificAvailability, WeeklyAvailability, ConsultationReason
from datetime import date, timedelta
from datetime import datetime, timedelta, date
from datetime import datetime, timedelta

# appointments/views.py

from django.shortcuts import render, get_object_or_404

def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    consultation_reasons = doctor.consultation_reasons.all()

    # Initialisation des variables de pré‑remplissage
    user_nom, user_prenom = '', ''
    user_email = ''
    user_phone = ''
    user_dob = None

    if request.user.is_authenticated:
        try:
            # Si l'utilisateur est un patient
            if hasattr(request.user, 'patient_profile'):
                patient = request.user.patient_profile
                user_nom    = patient.nom or ''
                user_prenom = patient.prenom or ''
            # Si l'utilisateur est un médecin
            elif hasattr(request.user, 'doctor_profile'):
                doc_prof = request.user.doctor_profile
                user_nom    = doc_prof.nom or ''
                user_prenom = doc_prof.prenom or ''

            # Champs toujours disponibles sur User
            user_email = request.user.email or ''
            user_phone = request.user.phone or ''
            user_dob   = request.user.date_of_birth  # peut être None ou un date object
        except Exception as e:
            # En cas d'erreur, on laisse les champs vides
            print(f"Erreur récupération profil : {e}")

    context = {
        'doctor': doctor,
        'consultation_reasons': consultation_reasons,
        # variables pour pré‑remplir le modal
        'user_nom'   : user_nom,
        'user_prenom': user_prenom,
        'user_email' : user_email,
        'user_phone' : user_phone,
        'user_dob'   : user_dob,
        'has_reasons': doctor.consultation_reasons.exists(),
        'default_duration': doctor.default_duration or 30,
    }
    return render(request, 'appointments/book.html', context)


def get_availabilities_api(request, doctor_id):
    """
    API pour récupérer les dates disponibles d'un médecin sous forme JSON.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)
    specific_availabilities = doctor.specific_availabilities.filter(is_active=True)

    # Générer les disponibilités sous forme JSON
    availabilities = [
        {"date": str(availability.date), "is_active": availability.is_active}
        for availability in specific_availabilities
    ]
    return JsonResponse({"availabilities": availabilities})

def get_available_times_api(request):
    """
    API pour récupérer les créneaux horaires disponibles pour une date donnée.
    Gère à la fois les créneaux normaux et urgents.
    """
    try:
        # 1. Extraction des paramètres
        is_emergency = request.GET.get('is_emergency', 'false') == 'true'
        date_str = request.GET.get("date")
        doctor_id = request.GET.get("doctor_id")
        consultation_reason_id = request.GET.get("consultation_reason_id")
        
        # 2. Validation des paramètres obligatoires
        if not date_str or not doctor_id:
            return JsonResponse(
                {"error": "Les paramètres 'date' et 'doctor_id' sont obligatoires"},
                status=400
            )

        # 3. Conversion de la date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse(
                {"error": "Format de date invalide. Utilisez 'YYYY-MM-DD'."},
                status=400
            )

        # 4. Récupération du médecin
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # 5. Détermination de la durée
        if is_emergency:
            slot_duration = getattr(doctor, 'default_duration', 30)
        elif consultation_reason_id:
            reason = get_object_or_404(ConsultationReason, id=consultation_reason_id, doctor=doctor)
            slot_duration = reason.duration
        else:
            slot_duration = getattr(doctor, 'default_duration', 30)

        # 6. Récupération des disponibilités
        availability = None

        if is_emergency:
            # ✅ Priorité aux disponibilités spécifiques
            availability = doctor.specific_availabilities.filter(
                date=date,
                is_active=True
            ).first()

            # ❌ Si aucune specific dispo, fallback sur weekly emergency
            if not availability:
                availability = doctor.weekly_availabilities.filter(
                    day=date.strftime("%A").lower(),
                    is_emergency=True
                ).first()
        else:
            # Cas normal : Specific > Weekly normale
            availability = doctor.specific_availabilities.filter(
                date=date,
                is_active=True
            ).first() or doctor.weekly_availabilities.filter(
                day=date.strftime("%A").lower(),
                is_emergency=False
            ).first()

        # 7. Génération des créneaux
        if availability:
            time_slots = generate_time_slots(
                availability.start_time,
                availability.end_time,
                slot_duration
            )
            available_times = filter_available_slots(doctor, date, time_slots, slot_duration)
            return JsonResponse({
                "available_times": available_times,
                "is_emergency": is_emergency  # Pour information frontend
            })

        return JsonResponse({"available_times": []})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def generate_time_slots(start_time, end_time, slot_duration=30):
    """
    Génère une liste de créneaux horaires entre start_time et end_time 
    en utilisant slot_duration (en minutes) comme intervalle.
    """
    slots = []
    current = datetime.combine(datetime.min.date(), start_time)
    end = datetime.combine(datetime.min.date(), end_time)

    while current + timedelta(minutes=slot_duration) <= end:
        slots.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=slot_duration)

    return slots


def filter_available_slots(doctor, date, time_slots, slot_duration):
    """
    Filtre les créneaux horaires pour exclure ceux qui se chevauchent avec des rendez-vous existants.
    Chaque créneau représenté par un horaire string est interprété comme un intervalle 
    [start, start + slot_duration] qui est comparé aux intervalles réservés.
    """
    # Récupérer tous les rendez-vous réservés pour ce médecin à la date donnée
    reserved_appointments = doctor.appointments.filter(date=date).exclude(status="cancelled")

    # Créer une liste d'intervalles réservés (datetime) : (start_datetime, end_datetime)
    reserved_intervals = []
    for app in reserved_appointments:
        start_dt = datetime.combine(date, app.time)
        end_dt = start_dt + timedelta(minutes=app.duration)  # app.duration contient généralement la durée du rendez-vous
        reserved_intervals.append((start_dt, end_dt))

    available = []
    # Pour chaque créneau généré (sous forme de chaîne "HH:MM")
    for slot_str in time_slots:
        slot_time = datetime.strptime(slot_str, "%H:%M").time()
        slot_start = datetime.combine(date, slot_time)
        slot_end = slot_start + timedelta(minutes=slot_duration)

        # Vérifier si ce créneau chevauche l'un des rendez-vous réservés
        conflict = False
        for r_start, r_end in reserved_intervals:
            # Les intervalles se chevauchent si:
            # slot_start < r_end et r_start < slot_end
            if slot_start < r_end and r_start < slot_end:
                conflict = True
                break
        if not conflict:
            available.append(slot_str)

    return available

# def get_available_dates_api_v2(request, doctor_id):
#     """
#     API pour récupérer les dates disponibles d'un médecin.
#     """
#     doctor = get_object_or_404(Doctor, id=doctor_id)
#     specific_availabilities = doctor.specific_availabilities.filter(is_active=True)

#     # Journaux pour diagnostic
#     print(f"Disponibilités actives pour le médecin {doctor_id} :")
#     for availability in specific_availabilities:
#         print(f"- {availability.date}, {availability.start_time}-{availability.end_time} (is_active={availability.is_active})")

#     # Préparer les disponibilités en JSON
#     available_dates = [
#         {"date": availability.date.isoformat(), "is_active": availability.is_active}
#         for availability in specific_availabilities
#     ]
#     return JsonResponse({"available_dates": available_dates})


def get_consultation_reasons(request, doctor_id):
    """
    API pour récupérer les motifs de consultation du médecin.
    Si aucun motif n'est défini, renvoie "has_reasons": False pour que le calendrier s'affiche directement.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)
    reasons = doctor.consultation_reasons.all()  # Utilise le related_name 'consultation_reasons'
    
    if reasons.exists():
        consultation_reasons = [
            {
                "id": reason.id,
                "name": reason.name,
                "duration": reason.duration,
                "description": reason.description
            }
            for reason in reasons
        ]
        return JsonResponse({"consultation_reasons": consultation_reasons, "has_reasons": True})
    else:
        # Aucun motif défini : on indique de passer directement au calendrier
        return JsonResponse({"consultation_reasons": [], "has_reasons": False})

from django.db.models import Q
from .models import WeeklyAvailability  # ou ajuste selon l'import réel

def get_combined_available_dates_api(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    today = date.today()

    minimum_delay = timedelta(days=doctor.minimum_delay if doctor.minimum_delay is not None else 1)
    maximum_delay = timedelta(days=doctor.maximum_delay if doctor.maximum_delay is not None else 90)
    min_date = today + minimum_delay
    max_date = today + maximum_delay

    specific_availabilities = doctor.specific_availabilities.filter(is_active=True, date__gte=min_date)
    specific_dates = {availability.date for availability in specific_availabilities}

    weekly_availabilities = doctor.weekly_availabilities.all()
    day_to_num = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
    }

    available_dates = set()
    emergency_dates = set()
    weeks_to_check = maximum_delay.days // 7

    for weekly in weekly_availabilities:
        target_weekday = day_to_num.get(weekly.day.lower())
        if target_weekday is None:
            continue

        delta_days = (target_weekday - today.weekday() + 7) % 7
        next_date = today + timedelta(days=delta_days)

        for i in range(weeks_to_check):
            date_occurrence = next_date + timedelta(weeks=i)
            if date_occurrence < min_date or date_occurrence > max_date:
                continue
            if date_occurrence not in specific_dates:
                available_dates.add(date_occurrence)

            # ✅ Ajoutons si ce créneau hebdo est marqué comme urgence
            if weekly.is_emergency:
                emergency_dates.add(date_occurrence)

    all_available_dates = sorted(specific_dates.union(available_dates))

    # Retourner les données sous forme JSON
    return JsonResponse({
        "available_dates": [
            {
                "date": dt.isoformat(),
                "is_specific": dt in specific_dates,
                "has_emergency": has_emergency_on_date(dt, doctor),  # <- à ajouter
                "has_non_emergency": has_non_emergency_on_date(dt, doctor)
            }
            for dt in all_available_dates
        ]
    })


def has_emergency_on_date(date_obj, doctor):
    weekday = date_obj.strftime('%A').lower()
    
    # Vérifie les créneaux hebdomadaires d'urgence
    weekly_emergency = doctor.weekly_availabilities.filter(
        day=weekday, is_emergency=True
    ).exists()

    # Vérifie les créneaux spécifiques si tu en as dans ton modèle (optionnel)
    # Si tu veux ignorer ça, retire cette partie
    specific_emergency = doctor.specific_availabilities.filter(
        date=date_obj, is_active=True
    ).exists()  # ← à personnaliser si tu veux un flag `is_emergency` dans les spécifiques aussi

    return weekly_emergency or specific_emergency

def has_non_emergency_on_date(date_obj, doctor):
    weekday = date_obj.strftime('%A').lower()
    
    # Vérifie les créneaux hebdomadaires normaux
    weekly_non_emergency = doctor.weekly_availabilities.filter(
        day=weekday, 
        is_emergency=False
    ).exists()

    # Vérifie les créneaux spécifiques non-urgents
    specific_non_emergency = doctor.specific_availabilities.filter(
        date=date_obj, 
        is_active=True
    ).exists()

    return weekly_non_emergency or specific_non_emergency

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from medecins.models import Doctor  # Import depuis l'app medecins
from .models import Appointment, ConsultationReason
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Appointment, ConsultationReason
from medecins.models import Doctor

User = get_user_model()

# @require_POST
# def confirm_appointment(request):
#     # 0. Vérifier la connexion
#     if not request.user.is_authenticated:
#         return JsonResponse({
#             'error': 'Vous devez vous connecter ou créer un compte pour prendre un rendez‑vous.'
#         }, status=401)

#     try:
#         # 1. Extraction des données
#         doctor_id       = request.POST.get('doctor_id')
#         date_str        = request.POST.get('date')
#         time_str        = request.POST.get('time')
#         is_urgence      = request.POST.get('is_urgence') == 'true'

#         # 2. Validation des champs obligatoires
#         if not all([doctor_id, date_str, time_str]):
#             return JsonResponse(
#                 {'error': 'Doctor ID, date et time sont requis.'},
#                 status=400
#             )

#         # 3. Conversion des dates
#         try:
#             date_obj = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#             time_obj = timezone.datetime.strptime(time_str, '%H:%M').time()
#         except ValueError:
#             return JsonResponse(
#                 {'error': 'Format de date (YYYY‑MM‑DD) ou heure (HH:MM) invalide.'},
#                 status=400
#             )

#         # 4. Récupération des objets
#         doctor = get_object_or_404(Doctor, id=doctor_id)
#         consultation_reason = None
#         if not is_urgence:
#             reason_id = request.POST.get('consultation_reason_id')
#             if reason_id:
#                 consultation_reason = get_object_or_404(
#                     ConsultationReason,
#                     id=reason_id,
#                     doctor=doctor
#                 )

#         # 5. Création du rendez-vous
#         appointment = Appointment(
#             doctor            = doctor,
#             patient           = request.user,  # on sait qu'il est authentifié
#             date              = date_obj,
#             time              = time_obj,
#             is_emergency      = is_urgence,
#             emergency_reason  = request.POST.get('urgence_details') if is_urgence else None,
#             consultation_reason = consultation_reason,
#             status            = 'pending'
#         )

#         # 6. Calcul automatique
#         if is_urgence:
#             appointment.duration = getattr(doctor, 'default_duration', 30)
#             appointment.prix     = float(doctor.prix or 0.00)
#         else:
#             appointment.prix = appointment.calculate_prix()

#         # 7. Validation & sauvegarde
#         appointment.full_clean()
#         appointment.save()

#         return JsonResponse({
#             'success'        : True,
#             'appointment_id' : appointment.id,
#             'date'           : date_str,
#             'time'           : time_str,
#             'is_emergency'   : is_urgence,
#             'doctor_name'    : f"{doctor.nom} {doctor.prenom}"
#         })

#     except ValidationError as e:
#         return JsonResponse({'error': e.message_dict or e.messages}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)






# appointments/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import json
from django.contrib.auth.decorators import login_required
from .models import Appointment, ConsultationReason
from medecins.models import Doctor
import logging
logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def confirm_appointment(request):
    try:
        logger.info("Requête reçue. Données brutes : %s", request.body)
        data = json.loads(request.body)  # Une seule ligne nécessaire
        try:
            datetime.strptime(data["time"], "%H:%M")
        except ValueError:
            raise ValidationError("Format de l'heure invalide. Utilisez HH:MM.")
        # Validation des champs obligatoires
        required_fields = ['doctor_id', 'date', 'time']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Champ manquant : {field}")

        # Récupération du médecin
        try:
            doctor = Doctor.objects.get(id=data['doctor_id'])
        except Doctor.DoesNotExist:
            logger.error("Médecin introuvable : ID %s", data['doctor_id'])
            return JsonResponse({'error': 'Médecin introuvable'}, status=404)

        # Validation motif/urgence
        if not data.get('is_urgence') and not data.get('reason_id'):
            if doctor.consultation_reasons.exists():
                raise ValidationError("Un motif de consultation est requis.")
            
        is_online = data.get('is_online', False)
        notes=data.get('notes', '')


        # Création du rendez-vous
        appointment = Appointment(
            doctor=doctor,
            patient=request.user,
            date=data['date'],
            time=data['time'],
            is_emergency=data.get('is_urgence', False),
            emergency_reason=data.get('urgence_details', '')[:500],
            consultation_reason_id=data.get('reason_id'),
            is_online=is_online,
            notes=notes
        )

        # Validation et sauvegarde
        appointment.full_clean()
        appointment.save()

        

        logger.info("Rendez-vous créé : ID %s", appointment.id)
        return JsonResponse({
            'success': True,
            'appointment_id': appointment.id,
            'doctor_name': f"{doctor.nom} {doctor.prenom}"
        })

    except json.JSONDecodeError as e:
        logger.error("Erreur de décodage JSON : %s", str(e))
        return JsonResponse({'error': 'Format JSON invalide'}, status=400)
        
    except ValidationError as e:
        logger.warning("Erreur de validation : %s", e.message_dict)
        return JsonResponse({'error': e.message_dict}, status=400)

    except Exception as e:
        logger.exception("Erreur inattendue : %s", str(e))
        return JsonResponse({'error': 'Erreur interne du serveur'}, status=500)


# appointments/views.py
from django.shortcuts import get_object_or_404
from .models import Appointment

def confirmation_page(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, "appointments/confirmation.html", {"appointment": appointment})

# def get_weekly_available_dates_api(request, doctor_id):
#     """
#     API pour récupérer les dates de travail d'un médecin en fonction de ses disponibilités hebdomadaires.
#     """
#     doctor = get_object_or_404(Doctor, id=doctor_id)
#     weekly_availabilities = doctor.weekly_availabilities.all()  # Accès via le related_name défini dans WeeklyAvailability

#     day_to_num = {
#         'monday': 0,
#         'tuesday': 1,
#         'wednesday': 2,
#         'thursday': 3,
#         'friday': 4,
#         'saturday': 5,
#         'sunday': 6
#     }

#     today = date.today()
#     available_dates = []
#     weeks_to_check = 4  # Calculer pour les 4 prochaines semaines

#     for weekly in weekly_availabilities:
#         target_weekday = day_to_num.get(weekly.day.lower(), None)
#         if target_weekday is None:
#             continue

#         # Calculer les dates correspondant au jour de disponibilité hebdomadaire
#         delta_days = (target_weekday - today.weekday() + 7) % 7
#         next_date = today + timedelta(days=delta_days)

#         for i in range(weeks_to_check):
#             date_occurrence = next_date + timedelta(weeks=i)
#             available_dates.append(date_occurrence.isoformat())  # Ajouter la date au format ISO

#     # Retourner toutes les dates de travail trouvées
#     return JsonResponse({"work_dates": sorted(available_dates)})

# views.py
# appointments/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from medecins.models import Doctor

@login_required
@require_GET
def get_doctor_info(request, doctor_id):
    """
    Renvoie en JSON les infos du médecin, notamment accept_online_appointments.
    """
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Médecin non trouvé'}, status=404)

    return JsonResponse({
        'id': doctor.id,
        'accept_online_appointments': doctor.accept_online_appointments,
    })

#---------------------------------------------------------------------------------------------------------
# PATIENT APPOINTMENTS:
#---------------------------------------------------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from patients.models import Patient
from django.contrib.auth import get_user_model
from patients.models import Patient
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def patient_appointments(request):
    """
    Affiche la liste des rendez-vous du patient connecté.
    """
    patient = request.user
    today = now().date()
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Utiliser `request.user` (objet User) pour la requête
    appointments = Appointment.objects.filter(
        patient=request.user,
        date__gte=today,
        is_online=False,
        is_emergency=False
    ).order_by('-date', '-time') if patient else []

    context = {
        'appointments': appointments,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/patient_appointments.html', context)

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime

@login_required
def cancel_appointment(request, appointment_id):
   
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Vérifiez que l'utilisateur connecté est autorisé à annuler ce rendez-vous
    if appointment.patient != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    # Changez le statut du rendez-vous pour "Annulé"
    appointment.status = 'cancelled'
    appointment.save()

    doctor = appointment.doctor
    appointment_datetime = datetime.combine(appointment.date, appointment.time)
    message = (
     f"Le patient {appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom} "
     f"a annulé le rendez-vous prévu le {appointment_datetime.strftime('%d/%m/%Y à %Hh%M')}."
    )
    send_notification(doctor.user, message)


    return JsonResponse({'success': 'Rendez-vous annulé'})



@login_required
def patient_teleconsultations(request):
    """
    Affiche la liste des téléconsultations (rendez-vous en ligne) du patient connecté.
    """
    patient = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    today = now().date()
    # Filtrer les rendez-vous en ligne associés à cet utilisateur (patient)
    teleconsultations = Appointment.objects.filter(patient=request.user,date__gte=today, is_online=True, is_emergency=False).order_by('-date', '-time') if patient else []

    context = {
        'teleconsultations': teleconsultations,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/patient_teleconsultations.html', context)

from django.http import Http404
@login_required
def appointment_detail(request, appointment_id):
    """
    Affiche le détail d'un rendez-vous pour l'utilisateur connecté.
    Gère les rôles de médecin et de patient.
    """

    try:
        
        # Récupérer le rendez-vous
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Vérifie que l'utilisateur connecté est autorisé à voir ce rendez-vous
        if appointment.patient != request.user and appointment.doctor.user != request.user:
            raise Http404("Vous n'êtes pas autorisé à accéder à ce rendez-vous.")

    except Appointment.DoesNotExist:
        raise Http404("Rendez-vous non trouvé ou non autorisé.")

    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Récupération des informations pour le profil (Patient ou Médecin)
    if hasattr(appointment.patient, 'patient_profile'):
        patient_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        role = "Patient"
    elif hasattr(appointment.patient, 'doctor_profile'):
        patient_name = f"Dr. {appointment.patient.doctor_profile.nom} {appointment.patient.doctor_profile.prenom}"
        role = "Médecin"
    else:
        patient_name = "Rôle inconnu"
        role = "Non défini"

    # Récupérer les autres informations nécessaires
    online_link = appointment.online_link if appointment.is_online else None
    doctor = appointment.doctor

    context = {
        'appointment': appointment,
        'patient_name': patient_name,
        'role': role,  # Ajoute le rôle pour le contexte
        'online_link': online_link,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/patient_appointment_details.html', context)


@login_required
def patient_urgent_appointments(request):
    """
    Affiche les urgences pour le patient connecté.
    """

    patient = request.user  # Le patient est l'utilisateur connecté
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    today = now().date()

    # Récupérer uniquement les rendez-vous urgents liés au patient
    urgent_appointments = Appointment.objects.filter(patient=patient,date__gte=today, is_emergency=True).order_by('-date', '-time')

    context = {
        'urgent_appointments': urgent_appointments,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/patient_urgent_appointments.html', context)


from django.utils.timezone import now
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def patient_appointment_history(request):
    """
    Vue pour afficher l'historique des rendez-vous du patient connecté.
    """
    patient = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    past_appointments = Appointment.objects.filter(
        patient=patient,
        date__lt=now().date()  # Inclut uniquement les rendez-vous passés
    ).order_by('-date', '-time')

    context = {
        'past_appointments': past_appointments,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/patient_appointment_history.html', context)


#---------------------------------------------------------------------------------------------------------
# DOCTOR APPOINTMENTS:
#---------------------------------------------------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from itertools import chain
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment

@login_required
def medcin_appointments(request):
    """
    Affiche uniquement les rendez-vous des patients avec le médecin connecté.
    """
    # Vérifier que l'utilisateur est bien un médecin
    if not hasattr(request.user, 'doctor_profile'):
        return HttpResponse("Vous devez être un médecin pour accéder à cette page.", status=403)

    # Récupérer le profil médecin
    doctor = request.user.doctor_profile
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    today = now().date()

    # Sélectionner uniquement les rendez-vous où ce médecin reçoit des patients
    as_doctor_appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gte=today,
        is_online=False,
        is_emergency=False
    ).order_by('-date', '-time')

    # Ajouter le nom et la photo du patient pour chaque rendez-vous
    for appointment in as_doctor_appointments:
        if hasattr(appointment.patient, 'patient_profile'):
            appointment.patient_full_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        else:
            appointment.patient_full_name = appointment.patient.username  # Si le patient n'a pas de profil spécifique
        
        # Ajoute la photo si disponible
        appointment.patient_photo = appointment.patient.profile_picture.url if hasattr(appointment.patient, 'profile_picture') and appointment.patient.profile_picture else None

    context = {
        'doctor_name': f"{doctor.nom} {doctor.prenom}",
        'profile_picture': request.user.profile_picture.url if hasattr(request.user, 'profile_picture') and request.user.profile_picture else None,
        'as_doctor_appointments': as_doctor_appointments,
        'unread_notification_count': unread_count,
    }
    
    return render(request, 'appointments/medcin_appointments.html', context)


@login_required
def doctor_appointment_detail(request, appointment_id):
    """
    Affiche les détails d'un rendez-vous pour le médecin connecté,
    y compris les informations sur le patient.
    """

    try:
        doctor = request.user.doctor_profile
    except AttributeError:
        doctor = None

    # Vérifier que le rendez-vous appartient bien au médecin connecté
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor) if doctor else None
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Ajoute une logique pour récupérer le nom et le prénom
   
    if hasattr(appointment.patient, 'patient_profile'):
        patient_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        compte_RIP = appointment.patient.patient_profile.compte_RIP or "Ce patient ne possède pas de compte RIP"
    
    else:
        patient_name = "Rôle inconnu"
        compte_RIP = "Ce patient ne possède pas de compte RIP"

    appointment.patient_photo = appointment.patient.profile_picture.url if appointment.patient.profile_picture else None
    online_link = appointment.online_link if appointment.is_online else None
    context = {
        'appointment': appointment,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'patient_name': patient_name,
        'online_link' : online_link,
        'compte_RIP' : compte_RIP,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/medcin_appointment_detail.html', context)


@login_required
def medcin_teleconsultations(request):
    """
    Affiche les téléconsultations :
    - En tant que médecin : téléconsultations où l'utilisateur est médecin.
    - En tant que patient : téléconsultations où l'utilisateur est patient avec d'autres médecins.
    """
    User = get_user_model()

    try:
        doctor = request.user.doctor_profile
        today = now().date()
    except AttributeError:
        doctor = None


    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Téléconsultations en tant que médecin
    as_doctor_teleconsultations = Appointment.objects.filter(doctor=doctor,date__gte=today, is_online=True, is_emergency=False).order_by('-date', '-time') if doctor else []

    # Téléconsultations en tant que patient
    as_patient_teleconsultations = Appointment.objects.filter(patient=request.user, is_online=True, is_emergency=False).order_by('-date', '-time')

    # Ajoute les noms complets et photos pour chaque rôle
    for teleconsultation in chain(as_doctor_teleconsultations, as_patient_teleconsultations):
        if hasattr(teleconsultation.patient, 'patient_profile'):
            teleconsultation.patient_full_name = f"{teleconsultation.patient.patient_profile.nom} {teleconsultation.patient.patient_profile.prenom}"
        elif hasattr(teleconsultation.patient, 'doctor_profile'):
            teleconsultation.patient_full_name = f"{teleconsultation.patient.doctor_profile.nom} {teleconsultation.patient.doctor_profile.prenom}"
        else:
            teleconsultation.patient_full_name = teleconsultation.patient.username
        
        # Ajoute la photo si disponible
        teleconsultation.patient_photo = teleconsultation.patient.profile_picture.url if hasattr(teleconsultation.patient, 'profile_picture') and teleconsultation.patient.profile_picture else None

    context = {
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'as_doctor_teleconsultations': as_doctor_teleconsultations,  # Téléconsultations en tant que médecin
        'as_patient_teleconsultations': as_patient_teleconsultations,  # Téléconsultations en tant que patient
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/medcin_teleconsultations.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Appointment
from .forms import ModifyAppointmentForm
from django.http import HttpResponseRedirect


@login_required
def modify_appointment(request, appointment_id):
    """
    Vue pour modifier un rendez-vous (statut, paiement, prix).
    """

    # Récupérer l'utilisateur en tant que médecin
    doctor = request.user.doctor_profile
    # Récupérer le rendez-vous correspondant
    appointment = get_object_or_404(Appointment, id=appointment_id)

    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Vérifier que l'utilisateur est le médecin du rendez-vous
    if appointment.doctor.user != request.user:
        return HttpResponseForbidden("Vous ne pouvez modifier que vos propres rendez-vous.")

    next_page = request.GET.get('next', None)  # Récupère la page d'origine

    # Récupérer l'ancienne valeur du statut avant toute modification
    old_status = appointment.status  # Ancien statut, avant modification du formulaire
    print(f"Ancien statut : {old_status}")
    old_price = appointment.prix  # Sauvegarde l'ancien prix
    print(f"Ancien prix : {old_price}")
    if appointment.is_online==True :
     old_teleconsultation_link = appointment.online_link


    if request.method == 'POST':
        form = ModifyAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            print(form.cleaned_data)
            # Nous devons d'abord récupérer l'ancienne valeur avant toute modification
            appointment = form.save(commit=False)  # Sauvegarde sans appliquer à la base
            # Récupérer la nouvelle valeur du statut
            new_status = form.cleaned_data['status']  # Nouveau statut après modification
            print(f"Nouveau statut : {new_status}")
            new_price = form.cleaned_data['prix']
            print(f"Nouveau prix : {new_price}")
            if appointment.is_online==True :
             new_teleconsultation_link = form.cleaned_data['online_link']

            # Enregistrer la modification dans la base de données
            
            appointment.save(skip_prix_calculation=True)

            # Vérifier si le statut a changé
            if old_status != new_status:
                print(f"Le statut a changé de {old_status} à {new_status}")
                appointment_datetime = datetime.combine(appointment.date, appointment.time)
                message = (
                  f"Votre rendez-vous avec Dr. {appointment.doctor.nom} {appointment.doctor.prenom} "
                  f"prévu le {appointment_datetime.strftime('%d/%m/%Y à %Hh%M')} est maintenant "
                  f"'{appointment.get_status_display()}'."
                )

                # Envoi de la notification à l'utilisateur (patient)
                print(f"Envoi de la notification à l'utilisateur : {appointment.patient}")
                send_notification(appointment.patient, message)  # Correctement accédé à l'utilisateur

            # Vérifier si le prix a changé
            if old_price != new_price:
                print(f"Le prix a changé de {old_price} à {new_price}")
                appointment_datetime = datetime.combine(appointment.date, appointment.time)
                message = (
                  f"Le prix de votre rendez-vous avec Dr. {appointment.doctor.nom} {appointment.doctor.prenom} "
                  f"prévu le {appointment_datetime.strftime('%d/%m/%Y à %Hh%M')} a été modifié à {new_price} DA."
                )
                send_notification(appointment.patient, message)

            if appointment.is_online==True :
                if old_teleconsultation_link != new_teleconsultation_link:
                    appointment_datetime = datetime.combine(appointment.date, appointment.time)
                    message = (
                    f"Le lien de téléconsultation pour votre rendez-vous avec Dr. {appointment.doctor.nom} {appointment.doctor.prenom}"
                    f"prévu le {appointment_datetime.strftime('%d/%m/%Y à %Hh%M')} a été mis à jour. "
                    f"Voici le lien : {new_teleconsultation_link}."
                    )
                    send_notification(appointment.patient, message)
                
            


            return HttpResponseRedirect(next_page) if next_page else redirect('appointments:medcin_appointments')
    else:
        form = ModifyAppointmentForm(instance=appointment)

    patient_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
    appointment.patient_photo = appointment.patient.profile_picture.url if appointment.patient.profile_picture else None

    context = {
        'form': form,
        'appointment': appointment,
        'patient_name': patient_name,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/medcin_appointment_modifier.html', context)



from core.models import Notification  # Import du modèle depuis core
from core.models import Notification  # Import du modèle depuis core
from patients.models import Patient  # Import du modèle Patient pour vérifier les notifications

from patients.models import Patient
from medecins.models import Doctor

def send_notification(user_or_profile, message):
    """
    Accepte un utilisateur ou un profil (Patient/Doctor) et envoie une notification.
    """
    

    # Si on reçoit un profil (Doctor ou Patient), on récupère le user
    if hasattr(user_or_profile, 'user'):
        user = user_or_profile.user
    else:
        user = user_or_profile

    try:
        patient = user.patient_profile
        if patient.notifications:
            Notification.objects.create(user=user, message=message)
            print("Notification envoyée au patient")
    except Patient.DoesNotExist:
        try:
            doctor = user.doctor_profile
            if doctor.notifications:
                Notification.objects.create(user=user, message=message)
                print("Notification envoyée au médecin")
        except Doctor.DoesNotExist:
            print("Utilisateur inconnu (ni patient ni médecin)")



from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from .models import WeeklyAvailability, SpecificAvailability
from .forms import WeeklyAvailabilityForm, SpecificAvailabilityForm
from django.core.exceptions import ValidationError

@login_required
def manage_availability(request):
    """
    Vue pour gérer les disponibilités hebdomadaires, spécifiques, et les horaires d'urgence d'un médecin connecté.
    """

    doctor = request.user.doctor_profile  # Profil du médecin connecté

    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Récupérer les disponibilités du médecin
    weekly_availabilities = WeeklyAvailability.objects.filter(doctor=doctor, is_emergency=False)
    specific_availabilities = SpecificAvailability.objects.filter(doctor=doctor)
    emergency_hours = WeeklyAvailability.objects.filter(doctor=doctor, is_emergency=True)

    # Initialiser les formulaires
    form_weekly = WeeklyAvailabilityForm(prefix='weekly')
    form_specific = SpecificAvailabilityForm(prefix='specific')
    form_emergency = WeeklyAvailabilityForm(prefix='emergency')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # Ajout de disponibilité hebdomadaire
        if form_type == 'weekly':
            form_weekly = WeeklyAvailabilityForm(request.POST, prefix='weekly')
            if form_weekly.is_valid():
                weekly = form_weekly.save(commit=False)
                weekly.doctor = doctor  # Associe le médecin connecté
                weekly.is_emergency = False
                try:
                    weekly.save()   # full_clean() + save()
                except ValidationError as e:
                    for msg in e.messages:
                        messages.error(request, msg)
                else:
                    messages.success(request, "Disponibilité hebdomadaire ajoutée avec succès.")
                    return redirect('appointments:manage_availability')
            else:
                for error in form_weekly.errors:
                  messages.error(request, form_weekly.errors[error])

        # Ajout de disponibilité spécifique
        elif form_type == 'specific':
            form_specific = SpecificAvailabilityForm(request.POST, prefix='specific')
            if form_specific.is_valid():
             specific = form_specific.save(commit=False)
             specific.doctor = doctor  # 👉 On affecte le docteur avant d'appeler full_clean() dans .save()
             try:
                 specific.full_clean()  # 👉 Appelle manuellement clean() du modèle pour éviter l'erreur
                 specific.save()
             except ValidationError as e:
                 for msg in e.messages:
                     messages.error(request, msg)
             else:
                 messages.success(request, "Disponibilité spécifique ajoutée avec succès.")
                 return redirect('appointments:manage_availability')
            else:
                for field, errors in form_specific.errors.items():
                 for error in errors:
                    # Si l'erreur est générale (non liée à un champ), ne pas afficher '__all__'
                   if field == '__all__':
                       messages.error(request, error)
                   else:
                       messages.error(request, f"{field} : {error}")

        # Ajout d'horaire d'urgence
        elif form_type == 'emergency':
            form_emergency = WeeklyAvailabilityForm(request.POST, prefix='emergency')
            if form_emergency.is_valid():
                emergency = form_emergency.save(commit=False)
                emergency.doctor = doctor  # Associe le médecin connecté
                emergency.is_emergency = True  # Marque comme urgence
                try:
                    emergency.save()
                except ValidationError as e:
                    for msg in e.messages:
                        messages.error(request, msg)
                else:
                    messages.success(request, "Horaires d'urgence ajoutés avec succès.")
                    return redirect('appointments:manage_availability')
            else:
                messages.error(request, "Erreur dans le formulaire des horaires d'urgence. Veuillez corriger.")

    context = {
        'weekly_availabilities': weekly_availabilities,
        'specific_availabilities': specific_availabilities,
        'emergency_hours': emergency_hours,
        'form_weekly': form_weekly,
        'form_specific': form_specific,
        'form_emergency': form_emergency,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/manage_availability.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import WeeklyAvailability
from .forms import WeeklyAvailabilityForm

@login_required
def edit_weekly_availability(request, availability_id):
    """
    Vue pour modifier une disponibilité hebdomadaire.
    """
    
    doctor = request.user.doctor_profile  # Profil du médecin connecté
    availability = get_object_or_404(WeeklyAvailability, id=availability_id, doctor=request.user.doctor_profile)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    if request.method == 'POST':
        form = WeeklyAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('appointments:manage_availability')
    else:
        form = WeeklyAvailabilityForm(instance=availability)

    context = {
        'form': form,
        'availability': availability,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/edit_weekly_availability.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import WeeklyAvailability
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages

@login_required
def delete_weekly_availability(request, availability_id):
    """
    Vue pour supprimer une disponibilité hebdomadaire.
    """
    
    doctor = request.user.doctor_profile  # Profil du médecin connecté

    # Récupérer la disponibilité et vérifier qu'elle appartient au médecin
    availability = get_object_or_404(WeeklyAvailability, id=availability_id, doctor=doctor)

    if request.method == 'POST':
        availability.delete()  # Supprimer la disponibilité
        messages.success(request, "Disponibilité supprimée avec succès.")
        return redirect('appointments:manage_availability')

    messages.error(request, "Action non autorisée.")
    return redirect('appointments:manage_availability')


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def delete_emergency_availability(request, availability_id):
    """
    Vue pour supprimer un horaire d'urgence.
    """
    
    doctor = request.user.doctor_profile  # Récupérer le profil du médecin connecté
    emergency = get_object_or_404(WeeklyAvailability, id=availability_id, doctor=doctor, is_emergency=True)

    if request.method == 'POST':
        emergency.delete()
        messages.success(request, "Horaire d'urgence supprimé avec succès.")
        return redirect('appointments:manage_availability')

    messages.error(request, "Action non autorisée.")
    return redirect('appointments:manage_availability')



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import SpecificAvailability
from .forms import SpecificAvailabilityForm

@login_required
def edit_specific_availability(request, availability_id):
    """
    Vue pour modifier une disponibilité spécifique.
    """
    
    doctor = request.user.doctor_profile
    # Récupérer la disponibilité spécifique
    availability = get_object_or_404(SpecificAvailability, id=availability_id)

    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Vérifier que l'utilisateur est bien le médecin associé à cette disponibilité
    if availability.doctor != request.user.doctor_profile:
        return HttpResponseForbidden("Vous n'avez pas les droits pour modifier cette disponibilité.")

    # Traitement du formulaire
    if request.method == 'POST':
        # Convertir la date au format ISO si nécessaire
        data = request.POST.copy()
        if 'date' in data and '/' in data['date']:  # Vérifie si le format est DD/MM/YYYY
            try:
                day, month, year = data['date'].split('/')
                data['date'] = f"{year}-{month}-{day}"  # Conversion en format ISO
            except ValueError:
                pass  # Ignorer si la conversion échoue

        form = SpecificAvailabilityForm(data, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('appointments:manage_availability')
    else:
        form = SpecificAvailabilityForm(instance=availability)

    # Contexte pour afficher le formulaire dans le template
    context = {
        'form': form,
        'availability': availability,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/edit_specific_availability.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def delete_specific_availability(request, availability_id):
    """
    Vue pour supprimer une disponibilité spécifique.
    """
    
    # Récupérer la disponibilité spécifique
    availability = get_object_or_404(SpecificAvailability, id=availability_id)

    # Vérifie que l'utilisateur est le médecin propriétaire
    if availability.doctor != request.user.doctor_profile:
        return HttpResponseForbidden("Vous ne pouvez pas supprimer cette disponibilité.")

    # Supprimer la disponibilité
    availability.delete()
    messages.success(request, "La disponibilité spécifique a été supprimée avec succès.")
    return redirect('appointments:manage_availability')


from .forms import ConsultationReasonForm


@login_required
def manage_consultation_reasons(request):
    
    doctor = request.user.doctor_profile
    reasons = ConsultationReason.objects.filter(doctor=doctor)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    if request.method == 'POST':
        form = ConsultationReasonForm(request.POST)
        if form.is_valid():
            reason = form.save(commit=False)
            reason.doctor = doctor
            reason.save()
            messages.success(request, "Motif de consultation ajouté avec succès.")
            return redirect('appointments:manage_consultation_reasons')
    else:
        form = ConsultationReasonForm()

    context = {
        'reasons': reasons,
        'form': form,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/manage_consultation_reasons.html', context)


@login_required
def edit_consultation_reason(request, reason_id):
    """
    Vue pour modifier un motif de consultation existant.
    """
    
    doctor = request.user.doctor_profile
    reason = get_object_or_404(ConsultationReason, id=reason_id)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Vérifie que le motif appartient au médecin connecté
    if reason.doctor != doctor:
        return HttpResponseForbidden("Vous n'avez pas les droits pour modifier ce motif.")

    # Traitement du formulaire
    if request.method == 'POST':
        form = ConsultationReasonForm(request.POST, instance=reason)
        if form.is_valid():
            form.save()
            messages.success(request, "Motif de consultation modifié avec succès.")
            return redirect('appointments:manage_consultation_reasons')
        else:
            messages.error(request, "Erreur lors de la modification. Veuillez corriger les erreurs.")
    else:
        form = ConsultationReasonForm(instance=reason)

    context = {
        'form': form,
        'reason': reason,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/edit_consultation_reason.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def delete_consultation_reason(request, reason_id):
    """
    Vue pour supprimer une raison de consultation.
    """
    
    reason = get_object_or_404(ConsultationReason, id=reason_id)

    if request.method == 'POST':
        reason.delete()
        messages.success(request, "Raison de consultation supprimée avec succès.")
        return redirect('appointments:manage_consultation_reasons')

    messages.error(request, "Action non autorisée.")
    return redirect('appointments:manage_consultation_reasons')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment

@login_required
def medcin_urgent_appointments(request):
    """
    Affiche les rendez-vous urgents pour le médecin connecté.
    """
    
    doctor = getattr(request.user, 'doctor_profile', None)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    today = now().date()

    if not doctor:
        return render(request, 'appointments/no_access.html', {'message': "Vous n'êtes pas autorisé à accéder à cette page."})

    # Récupérer uniquement les rendez-vous urgents liés au médecin connecté
    # Rendez-vous urgents en tant que médecin
    as_doctor_urgent_appointments = Appointment.objects.filter(doctor=doctor,date__gte=today, is_emergency=True).order_by('-date', '-time')

    # Rendez-vous urgents en tant que patient
    as_patient_urgent_appointments = Appointment.objects.filter(patient=request.user, is_emergency=True).order_by('-date', '-time')

    for appointment in chain(as_doctor_urgent_appointments, as_patient_urgent_appointments):
        if hasattr(appointment.patient, 'patient_profile'):
            appointment.patient_full_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        elif hasattr(appointment.patient, 'doctor_profile'):  # Si le patient est un médecin
            appointment.patient_full_name = f"{appointment.patient.doctor_profile.nom} {appointment.patient.doctor_profile.prenom}"
        else:
            appointment.patient_full_name = appointment.patient.username
    
        appointment.patient_photo = appointment.patient.profile_picture.url if hasattr(appointment.patient, 'profile_picture') and appointment.patient.profile_picture else None

    context = {
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else None,
        'as_doctor_urgent_appointments': as_doctor_urgent_appointments,  # Urgents où il est médecin
        'as_patient_urgent_appointments': as_patient_urgent_appointments,  # Urgents où il est patient
        'profile_picture': request.user.profile_picture.url if hasattr(request.user, 'profile_picture') and request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/medcin_urgent_appointments.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.core.exceptions import PermissionDenied
from appointments.models import Appointment
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

@login_required
def doctor_appointment_history(request):
    """
    Vue pour afficher l'historique des rendez-vous du médecin connecté.
    """
    # Récupérer l'instance Doctor associée à l'utilisateur connecté
    doctor_instance = get_object_or_404(Doctor, user=request.user)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    # Filtrer les rendez-vous passés liés au médecin
    past_appointments = Appointment.objects.filter(
        doctor=doctor_instance,  # Passe une instance de Doctor ici
        date__lt=now().date()  # Inclut uniquement les rendez-vous passés
    ).order_by('-date', '-time')

    for appointment in past_appointments:
        appointment.patient_full_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
    context = {
        'past_appointments': past_appointments,
        'doctor_name': f"{doctor_instance.nom} {doctor_instance.prenom}",
        'profile_picture': doctor_instance.user.profile_picture.url if doctor_instance.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'appointments/medcin_appointment_history.html', context)



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import Notification  # si le modèle est bien dans core
from medecins.models import Doctor

@login_required
def doctor_notifications(request):
    doctor = Doctor.objects.get(user=request.user)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    notifications = Notification.objects.filter(user=request.user).order_by('-sent_at')[:50]
    return render(request, 'appointments/doctor_notifications.html', {
        'notifications': notifications,'unread_notification_count': unread_count,
        'doctor_name': f"{request.user.doctor_profile.nom} {request.user.doctor_profile.prenom}" if doctor else None
    })


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from core.models import Notification  # assuming your Notification model is in app 'core'

@login_required
def doctor_mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.status = 'read'
    notification.save()
    return JsonResponse({'status': 'success'})


@login_required
def doctor_delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'success'})


@login_required
def doctor_mark_all_notifications_as_read(request):
    Notification.objects.filter(user=request.user, status='unread').update(status='read')
    return JsonResponse({'status': 'success'})


@login_required
def doctor_delete_all_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'success'})
