from django.shortcuts import render, get_object_or_404
from medecins.models import Doctor
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from appointments.models import Appointment, SpecificAvailability, WeeklyAvailability, ConsultationReason
from datetime import date, timedelta
from datetime import datetime, timedelta, date
from datetime import datetime, timedelta


def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    consultation_reasons = doctor.consultation_reasons.all()

    user_nom, user_prenom = None, None
    if request.user.is_authenticated:
        try:
            # Si l'utilisateur est un patient
            if hasattr(request.user, 'patient_profile'):  # Vérifie la relation avec le modèle Patient
                patient = request.user.patient_profile
                user_nom = patient.nom
                user_prenom = patient.prenom
            # Si l'utilisateur est un médecin
            elif hasattr(request.user, 'doctor'):  # Vérifie la relation avec le modèle Doctor
                doctor_profile = request.user.doctor
                user_nom = doctor_profile.nom
                user_prenom = doctor_profile.prenom
        except Exception as e:
            print(f"Erreur lors de la récupération du profil : {e}")

    context = {
        'doctor': doctor,
        'consultation_reasons': consultation_reasons,
        'user_nom': user_nom,
        'user_prenom': user_prenom,
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
    API pour récupérer les créneaux horaires disponibles pour une date donnée,
    en utilisant la durée du motif de consultation sélectionné si fourni,
    sinon en utilisant la durée par défaut du médecin.
    """
    try:
        # Récupération des paramètres GET
        date_str = request.GET.get("date")
        doctor_id = request.GET.get("doctor_id")
        consultation_reason_id = request.GET.get("consultation_reason_id")
        
        if not date_str or not doctor_id:
            return JsonResponse(
                {"error": "Les paramètres 'date' et 'doctor_id' sont obligatoires"},
                status=400
            )

        # Validation de la date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse(
                {"error": "Format de date invalide. Utilisez 'YYYY-MM-DD'."},
                status=400
            )

        # Récupération du médecin
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Déterminer la durée à utiliser pour le créneau
        if consultation_reason_id:
            # Récupérer le motif et utiliser sa durée (en minutes)
            reason = get_object_or_404(ConsultationReason, id=consultation_reason_id, doctor=doctor)
            slot_duration = reason.duration
        else:
            # Utiliser la durée par défaut du médecin (ici 30 minutes si non défini)
            slot_duration = getattr(doctor, 'default_duration', 30)

        # Recherche des disponibilités spécifiques pour la date donnée
        specific = doctor.specific_availabilities.filter(date=date, is_active=True).first()
        if specific:
            time_slots = generate_time_slots(specific.start_time, specific.end_time, slot_duration)
            available_times = filter_available_slots(doctor, date, time_slots, slot_duration)
            return JsonResponse({"available_times": available_times})

        # Recherche des disponibilités hebdomadaires pour le jour de la semaine correspondant
        weekly = doctor.weekly_availabilities.filter(day=date.strftime("%A").lower()).first()
        if weekly:
            time_slots = generate_time_slots(weekly.start_time, weekly.end_time, slot_duration)
            available_times = filter_available_slots(doctor, date, time_slots, slot_duration)
            return JsonResponse({"available_times": available_times})

        # Si aucune disponibilité n'est trouvée, retourner une liste vide
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
    reserved_appointments = doctor.appointments.filter(date=date)

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


def get_combined_available_dates_api(request, doctor_id):
    """
    API pour récupérer toutes les dates disponibles d'un médecin en combinant
    les disponibilités spécifiques et hebdomadaires, tout en respectant les
    délais définis par le médecin.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)
    today = date.today()

    # Récupérer les délais personnalisés du médecin ou appliquer des valeurs par défaut
    minimum_delay = timedelta(days=doctor.minimum_delay if doctor.minimum_delay is not None else 1)
    maximum_delay = timedelta(days=doctor.maximum_delay if doctor.maximum_delay is not None else 90)
    min_date = today + minimum_delay
    max_date = today + maximum_delay

    # Récupérer les disponibilités spécifiques actives après le délai minimum
    specific_availabilities = doctor.specific_availabilities.filter(is_active=True, date__gte=min_date)
    specific_dates = {availability.date for availability in specific_availabilities}

    # Récupérer les disponibilités hebdomadaires
    weekly_availabilities = doctor.weekly_availabilities.all()
    day_to_num = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6,
    }

    available_dates = set()
    weeks_to_check = maximum_delay.days // 7  # Convertir le délai maximum en semaines

    for weekly in weekly_availabilities:
        target_weekday = day_to_num.get(weekly.day.lower())
        if target_weekday is None:
            continue

        # Calcul des occurrences hebdomadaires
        delta_days = (target_weekday - today.weekday() + 7) % 7
        next_date = today + timedelta(days=delta_days)

        for i in range(weeks_to_check):
            date_occurrence = next_date + timedelta(weeks=i)
            # Vérifier si la date est hors des limites définies
            if date_occurrence < min_date or date_occurrence > max_date:
                continue
            # Vérifier si une disponibilité spécifique existe déjà
            if date_occurrence not in specific_dates:
                available_dates.add(date_occurrence)

    # Convertir les ensembles en liste triée
    all_available_dates = sorted(specific_dates.union(available_dates))

    # Retourner les données sous forme JSON
    return JsonResponse({
        "available_dates": [
            {"date": dt.isoformat(), "is_specific": dt in specific_dates}
            for dt in all_available_dates
        ]
    })


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



#---------------------------------------------------------------------------------------------------------
# PATIENT APPOINTMENTS:
#---------------------------------------------------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from patients.models import Patient
from django.contrib.auth import get_user_model
from patients.models import Patient

@login_required
def patient_appointments(request):
    """
    Affiche la liste des rendez-vous du patient connecté.
    """
    User = get_user_model()#pour tester

    try:
        #pour tester----------------------------------------------------------------------------------------
        # Simuler un patient spécifique pour le test
        test_user = User.objects.get(email="patient1@exemple.com")  # Remplace avec un email valide
        request.user = test_user  # Simule la connexion du patient dans la vue
        #---------------------------------------------------------------------------------------------------

        # Récupérer le profil patient
        patient = request.user.patient_profile  # Accès via related_name
    except Patient.DoesNotExist:
        patient = None

    # Utiliser `request.user` (objet User) pour la requête
    appointments = Appointment.objects.filter(
        patient=request.user,
        is_online=False  # <-- Ajout de ce filtre
    ).order_by('-date', '-time') if patient else []

    context = {
        'appointments': appointments,
        'nom': patient.nom if patient else None,
        'prenom': patient.prenom if patient else None,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
    }
    return render(request, 'appointments/patient_appointments.html', context)

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
@login_required
def cancel_appointment(request, appointment_id):
    User = get_user_model()  # Pour le test

    try:
        # Simuler un patient spécifique pour le test
        test_user = User.objects.get(email="patient1@exemple.com")  # Remplacez par un email valide
        request.user = test_user  # Simule la connexion du patient
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur de test non trouvé'}, status=404)

    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Vérifiez que l'utilisateur connecté est autorisé à annuler ce rendez-vous
    if appointment.patient != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    # Changez le statut du rendez-vous pour "Annulé"
    appointment.status = 'Annulé'
    appointment.save()

    return JsonResponse({'success': 'Rendez-vous annulé'})


@login_required
def patient_teleconsultations(request):
    """
    Affiche la liste des téléconsultations (rendez-vous en ligne) du patient connecté.
    """
    User = get_user_model() #pour tester
    try:
        #pour tester----------------------------------------------------------------------------------------
        # Simuler un patient spécifique pour le test
        test_user = User.objects.get(email="patient1@exemple.com")  # Remplace avec un email valide
        request.user = test_user  # Simule la connexion du patient dans la vue
        #---------------------------------------------------------------------------------------------------

        # Récupérer l'utilisateur en tant que patient
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        patient = None

    # Filtrer les rendez-vous en ligne associés à cet utilisateur (patient)
    teleconsultations = Appointment.objects.filter(patient=request.user, is_online=True).order_by('-date', '-time') if patient else []

    context = {
        'teleconsultations': teleconsultations,
        'patient_name': f"{patient.nom} {patient.prenom}" if patient else "Patient inconnu"
    }
    return render(request, 'appointments/patient_teleconsultations.html', context)

from django.http import Http404

@login_required
def appointment_detail(request, appointment_id):
    """
    Affiche le détail d'un rendez-vous pour l'utilisateur connecté.
    """
    User = get_user_model() #pour tester
    try:
        #pour tester----------------------------------------------------------------------------------------
        # Simuler un patient spécifique pour le test
        test_user = User.objects.get(email="patient1@exemple.com")  # Remplace avec un email valide
        request.user = test_user  # Simule la connexion du patient dans la vue
        #---------------------------------------------------------------------------------------------------

        # Récupérer le rendez-vous correspondant au patient connecté
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    except Appointment.DoesNotExist:
        raise Http404("Rendez-vous non trouvé ou non autorisé.")

    online_link = appointment.online_link if appointment.is_online else None
    doctor = appointment.doctor

    context = {
        'appointment': appointment,
        'latitude': doctor.latitude,
        'longitude': doctor.longitude,
        'patient_name': f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}" if hasattr(appointment.patient, 'patient_profile') else "Patient inconnu",
        'online_link': online_link,
    }
    return render(request, 'appointments/patient_appointment_details.html', context)




#---------------------------------------------------------------------------------------------------------
# DOCTOR APPOINTMENTS:
#---------------------------------------------------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from itertools import chain

@login_required
def medcin_appointments(request):
    """
    Affiche les rendez-vous liés au médecin connecté.
    - En tant que médecin : rendez-vous des patients avec lui.
    - En tant que patient : rendez-vous pris par ce médecin chez d'autres médecins.
    """
    User = get_user_model()

    try:
        # Simuler un médecin pour le test
        test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace avec un email valide
        request.user = test_user  # Simule la connexion du médecin

        # Récupérer le médecin
        doctor = request.user.doctor_profile
    except AttributeError:
        doctor = None

    # Rendez-vous en tant que médecin
    as_doctor_appointments = Appointment.objects.filter(doctor=doctor, is_online=False).order_by('-date', '-time') if doctor else []

    # Rendez-vous en tant que patient
    as_patient_appointments = Appointment.objects.filter(patient=request.user, is_online=False).order_by('-date', '-time')

    # Utilisation de itertools.chain pour fusionner les deux QuerySet (sans affecter le résultat du rendu)
    all_appointments = chain(as_doctor_appointments, as_patient_appointments)

    # Ajoute le nom complet pour les patients ou médecins selon leur rôle
    for appointment in all_appointments:
        if hasattr(appointment.patient, 'patient_profile'):
            appointment.patient_full_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        elif hasattr(appointment.patient, 'doctor_profile'):
            appointment.patient_full_name = f"{appointment.patient.doctor_profile.nom} {appointment.patient.doctor_profile.prenom}"
        else:
            appointment.patient_full_name = "Rôle inconnu"

        # Ajoute la photo si disponible
        appointment.patient_photo = appointment.patient.profile_picture.url if hasattr(appointment.patient, 'profile_picture') and appointment.patient.profile_picture else None

    context = {
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
        'profile_picture': request.user.profile_picture.url if hasattr(request.user, 'profile_picture') and request.user.profile_picture else None,
        'as_doctor_appointments': as_doctor_appointments,  # Rendez-vous en tant que médecin
        'as_patient_appointments': as_patient_appointments,  # Rendez-vous en tant que patient
    }
    return render(request, 'appointments/medcin_appointments.html', context)


@login_required
def doctor_appointment_detail(request, appointment_id):
    """
    Affiche les détails d'un rendez-vous pour le médecin connecté,
    y compris les informations sur le patient.
    """
    User = get_user_model()  # Pour tester uniquement

    try:
        # Simuler un médecin pour le test
        test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace avec l'email valide
        request.user = test_user  # Simule la connexion du médecin pour cette vue

        # Récupérer le médecin
        doctor = request.user.doctor_profile
    except AttributeError:
        doctor = None

    # Vérifier que le rendez-vous appartient bien au médecin connecté
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor) if doctor else None

    # Ajoute une logique pour récupérer le nom et le prénom
   
    if hasattr(appointment.patient, 'patient_profile'):
        patient_name = f"{appointment.patient.patient_profile.nom} {appointment.patient.patient_profile.prenom}"
        compte_RIP = appointment.patient.patient_profile.compte_RIP or "Ce patient ne possède pas de compte RIP"
    elif hasattr(appointment.patient, 'doctor_profile'):
        patient_name = f"{appointment.patient.doctor_profile.nom} {appointment.patient.doctor_profile.prenom}"
        compte_RIP = appointment.patient.doctor_profile.compte_RIP or "Ce patient ne possède pas de compte RIP"
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
    }
    return render(request, 'appointments/medcin_appointment_detail.html', context)



@login_required
def medcin_teleconsultations(request):
    """
    Affiche la liste des téléconsultations (rendez-vous en ligne) du médecin connecté.
    """
    User = get_user_model()  # Pour tester

    try:
        # Simuler un médecin pour le test
        test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
        request.user = test_user  # Simule la connexion du médecin dans la vue

        # Récupérer l'utilisateur en tant que médecin
        doctor = request.user.doctor_profile
    except AttributeError:
        doctor = None

    # Filtrer les téléconsultations associées au médecin
    teleconsultations = Appointment.objects.filter(doctor=doctor, is_online=True).order_by('-date', '-time') if doctor else []

    # Ajoute une logique pour récupérer le nom et le prénom
    for teleconsultation in teleconsultations:
        if hasattr(teleconsultation.patient, 'patient_profile'):
            # Si l'utilisateur a un profil Patient
            teleconsultation.patient_full_name = f"{teleconsultation.patient.patient_profile.nom} {teleconsultation.patient.patient_profile.prenom}"
        elif hasattr(teleconsultations.patient, 'doctor_profile'):
            # Si l'utilisateur a un profil Médecin
            teleconsultation.patient_full_name = f"{teleconsultation.patient.doctor_profile.nom} {teleconsultation.patient.doctor_profile.prenom}"
        else:
            # Si le rôle est inconnu
            teleconsultation.patient_full_name = "Rôle inconnu"

    teleconsultation.patient_photo = teleconsultation.patient.profile_picture.url if teleconsultation.patient.profile_picture else None
    context = {
        'teleconsultations': teleconsultations,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
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

    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user  # Simule la connexion du médecin dans la vue

        # Récupérer l'utilisateur en tant que médecin
    doctor = request.user.doctor_profile
    # Récupérer le rendez-vous correspondant
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Vérifier que l'utilisateur est le médecin du rendez-vous
    if appointment.doctor.user != request.user:
        return HttpResponseForbidden("Vous ne pouvez modifier que vos propres rendez-vous.")

    next_page = request.GET.get('next', None)  # Récupère la page d'origine

    if request.method == 'POST':
        form = ModifyAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            # Sauvegarde sans recalcul du prix
            form.save(commit=False)  # Ne sauvegarde pas immédiatement
            appointment.save(skip_prix_calculation=True)  # Bypass le calcul du prix
            if next_page:
                return HttpResponseRedirect(next_page)
            else:
                return redirect('appointments:medcin_appointments')  # Redirige par défaut
    else:
        form = ModifyAppointmentForm(instance=appointment)

    context = {
        'form': form,
        'appointment': appointment,
        'doctor_name': f"{doctor.nom} {doctor.prenom}" if doctor else "Médecin inconnu",
    }
    return render(request, 'appointments/medcin_appointment_modifier.html', context)


from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from .models import WeeklyAvailability, SpecificAvailability
from .forms import WeeklyAvailabilityForm, SpecificAvailabilityForm
@login_required
def manage_availability(request):
    """
    Vue pour gérer les disponibilités hebdomadaires, spécifiques, et les horaires d'urgence d'un médecin connecté.
    """
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    doctor = request.user.doctor_profile  # Profil du médecin connecté

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
                weekly.save()  # Enregistre après avoir ajouté `doctor`
                messages.success(request, "Disponibilité hebdomadaire ajoutée avec succès.")
                return redirect('appointments:manage_availability')
            else:
                messages.error(request, "Erreur dans le formulaire hebdomadaire. Veuillez corriger.")

        # Ajout de disponibilité spécifique
        elif form_type == 'specific':
            form_specific = SpecificAvailabilityForm(request.POST, prefix='specific')
            if form_specific.is_valid():
                specific = form_specific.save(commit=False)
                specific.doctor = doctor  # Associe le médecin connecté
                specific.save()
                messages.success(request, "Disponibilité spécifique ajoutée avec succès.")
                return redirect('appointments:manage_availability')
            else:
                messages.error(request, "Erreur dans le formulaire spécifique. Veuillez corriger.")

        # Ajout d'horaire d'urgence
        elif form_type == 'emergency':
            form_emergency = WeeklyAvailabilityForm(request.POST, prefix='emergency')
            if form_emergency.is_valid():
                emergency = form_emergency.save(commit=False)
                emergency.doctor = doctor  # Associe le médecin connecté
                emergency.is_emergency = True  # Marque comme urgence
                emergency.save()
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
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    doctor = request.user.doctor_profile  # Profil du médecin connecté
    availability = get_object_or_404(WeeklyAvailability, id=availability_id, doctor=request.user.doctor_profile)

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
    User = get_user_model()  # Simule un utilisateur pour les tests
    test_user = User.objects.get(email="medcin3@exemple.com")  # Médecin connecté
    request.user = test_user
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
    User = get_user_model()  # Simule un utilisateur pour les tests
    test_user = User.objects.get(email="medcin3@exemple.com")  # Médecin connecté
    request.user = test_user
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
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    doctor = request.user.doctor_profile
    # Récupérer la disponibilité spécifique
    availability = get_object_or_404(SpecificAvailability, id=availability_id)

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
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
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
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    doctor = request.user.doctor_profile
    reasons = ConsultationReason.objects.filter(doctor=doctor)

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
    }
    return render(request, 'appointments/manage_consultation_reasons.html', context)


@login_required
def edit_consultation_reason(request, reason_id):
    """
    Vue pour modifier un motif de consultation existant.
    """
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    doctor = request.user.doctor_profile
    reason = get_object_or_404(ConsultationReason, id=reason_id)

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
    }
    return render(request, 'appointments/edit_consultation_reason.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def delete_consultation_reason(request, reason_id):
    """
    Vue pour supprimer une raison de consultation.
    """
    User = get_user_model()  # Pour tester
    test_user = User.objects.get(email="medcin3@exemple.com")  # Remplace par un email valide
    request.user = test_user
    reason = get_object_or_404(ConsultationReason, id=reason_id)

    if request.method == 'POST':
        reason.delete()
        messages.success(request, "Raison de consultation supprimée avec succès.")
        return redirect('appointments:manage_consultation_reasons')

    messages.error(request, "Action non autorisée.")
    return redirect('appointments:manage_consultation_reasons')
