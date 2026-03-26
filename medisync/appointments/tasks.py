from django.utils import timezone
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from appointments.models import Appointment

def send_rappel_emails():
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)

    # Version ultra-sécurisée avec préchargement optimal
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status='confirmed'
    ).select_related(
        'patient',          # Charge le User patient
        'doctor',           # Charge le modèle Doctor
    )

    for appt in appointments:
        try:
            # 1. INFOS PATIENT (accès direct)
            email = appt.patient.email  # Email directement depuis User
            
            # Accès sécurisé au profil patient
            try:
                patient_profile = appt.patient.patient_profile
                patient_name = f"{patient_profile.nom} {patient_profile.prenom}"
            except ObjectDoesNotExist:
                print(f"Profil patient manquant pour {appt.patient.id}")
                continue

            # 2. INFOS DOCTEUR (accès direct)
            doctor_name = f"Dr. {appt.doctor.nom} {appt.doctor.prenom}"  # Champ direct dans Doctor

            # 3. FORMATAGE DATE/HEURE
            date_str = appt.date.strftime('%d/%m/%Y')
            time_str = appt.time.strftime('%H:%M')

            # 4. ENVOI EMAIL
            subject = f"📅 Rappel : Rendez-vous le {date_str}"
            message = (
                f"Bonjour {patient_name},\n\n"
                f"Ceci est un rappel pour votre rendez-vous avec {doctor_name} "
                f"le {date_str} à {time_str}.\n\n"
                f"Merci d'utiliser Medisync."
            )

            send_mail(subject, message, 'medisyncsite@gmail.com', [email])

        except Exception as e:
            print(f"Erreur pour le RDV {appt.id}: {str(e)}")
            continue