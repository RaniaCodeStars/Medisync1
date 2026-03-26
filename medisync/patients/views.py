from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.shortcuts import render
from django.utils.timezone import now
from appointments.models import Appointment
from core.models import Notification
from patients.models import PatientDocument
from messaging.models import Message 

def patient_dashboard(request):
    """
    Vue pour afficher le tableau de bord du patient.
    """
    patient = request.user
    
    today = now().date()

    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    unread_messages_count = Message.objects.filter(receiver=patient, is_read=False).count()

    # Total des rendez-vous en attente
    total_pending = Appointment.objects.filter(patient=patient, status='pending').count()

    # Total des rendez-vous confirmés à venir
    total_upcoming = Appointment.objects.filter(patient=patient, status='confirmed', date__gte=today).count()

    # Rendez-vous d'aujourd'hui
    today_appointments = Appointment.objects.filter(patient=patient, status='confirmed', date=today).order_by('time')

    # Premier prochain rendez-vous
    next_date_appointments = (
        Appointment.objects.filter(patient=patient, status='confirmed', date__gt=today)
        .order_by('date', 'time')
        .first()
    )
    next_appointments = []
    if next_date_appointments:
        next_appointments = Appointment.objects.filter(
            patient=patient,
            status='confirmed',
            date=next_date_appointments.date
        ).order_by('time')

    total_documents = PatientDocument.objects.filter(patient=patient).count()

    context = {
        'total_pending': total_pending,
        'total_upcoming': total_upcoming,
        'today_appointments': today_appointments,
        'next_appointments': next_appointments,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
        'total_documents': total_documents,  
        'unread_messages_count': unread_messages_count,
    }
    return render(request, 'patients/patient_dashboard.html', context)


#------------------------------------------------------------------------------------------------------------------
# Documents
#------------------------------------------------------------------------------------------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import PatientDocument
from .forms import PatientDocumentForm

@login_required
def patient_documents(request):
    """
    Vue permettant d'afficher et ajouter des documents.
    """
    user = request.user  # Celui qui est connecté (uploaded_by)
    try:
        patient = request.user.patient_profile  # S'il est lui-même patient
    except:
        patient = None

    documents = PatientDocument.objects.filter(patient=user)
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    if request.method == "POST":
        form = PatientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.patient = user  # ou document.patient = patient.user si nécessaire
            document.uploaded_by = user  # 🔥 c’est ici que tu définis l'auteur du document
            document.save()
            return redirect('patients:patient_documents')
    else:
        form = PatientDocumentForm()

    context = {
      'documents': documents,
      'form': form,
      'patient_name': f"{patient.nom} {patient.prenom}" if patient else user.username,
      'profile_picture': request.user.profile_picture.url if getattr(request.user, 'profile_picture', None) else None,
      'unread_notification_count': unread_count,
    }

    return render(request, 'patients/patient_documents.html', context)


@login_required
def delete_document(request, document_id):
    """
    Supprime un document du patient.
    """
    document = get_object_or_404(PatientDocument, id=document_id, patient=request.user)
    document.delete()
    return redirect('patients:patient_documents')

@login_required
def download_document(request, document_id):
    """
    Télécharge un document.
    """
    document = get_object_or_404(PatientDocument, id=document_id, patient=request.user)
    response = HttpResponse(document.document, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.document.name}"'
    return response

#------------------------------------------------------------------------------------------------------------------
# Parametre
#------------------------------------------------------------------------------------------------------------------

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def patient_settings(request):
    """
    Vue pour afficher la page des paramètres du patient.
    """
    patient = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    
    context = {
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if getattr(request.user, 'profile_picture', None) else None,
        'edit_profile_url': 'patients:patient_edit_profile',  # URL pour modifier le profil
        'unread_notification_count': unread_count,
        'appointments_history_url': 'appointments:patient_appointment_history',  # URL pour l'historique des rendez-vous
    }
    return render(request, 'patients/patient_settings.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def edit_profile(request):
    """
    Vue pour modifier le profil du patient.
    """
    patient = request.user.patient_profile
    user = request.user
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    
    if request.method == 'POST':
        patient.nom = request.POST.get('nom')
        patient.prenom = request.POST.get('prenom')
        patient.blood_group = request.POST.get('blood_group')
        patient.weight = float(request.POST.get('weight')) if request.POST.get('weight') else None
        patient.height = float(request.POST.get('height')) if request.POST.get('height') else None
        patient.allergies = request.POST.get('allergies') if request.POST.get('allergies') else None
        patient.compte_RIP = request.POST.get('compte_RIP')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')
        user.city = request.POST.get('city')
        user.country = request.POST.get('country')
        user.date_of_birth = request.POST.get('date_of_birth') if request.POST.get('date_of_birth') else None

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        patient.save()

        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('patients:patient_settings')
    
    # Préparation du contexte (version simplifiée)
    context = {
        'patient': patient,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    
    return render(request, 'patients/patient_edit_profile.html', context)


#------------------------------------------------------------------------------------------------------------------
# Notification
#------------------------------------------------------------------------------------------------------------------

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Notification  # Import du modèle depuis core
@login_required
def patient_notification_list(request):
    """
    Vue pour afficher les notifications du patient connecté.
    """
    patient = request.user
    notifications = Notification.objects.filter(user=request.user).order_by('-sent_at')  # Trier par date
    unread_count = Notification.objects.filter(user=request.user, status='unread').count()

    context = {
        'notifications': notifications,
        'patient_name': f"{patient.patient_profile.nom} {patient.patient_profile.prenom}" if hasattr(patient, 'patient_profile') else patient.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        'unread_notification_count': unread_count,
    }
    return render(request, 'patients/patient_notification_list.html', context)  # Nouveau template


# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Patient

@login_required
def toggle_notifications(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        patient = Patient.objects.get(user=request.user)
        enabled = request.POST.get('enabled') == 'true'
        patient.notifications = enabled
        patient.save()
        return JsonResponse({'status': 'success', 'enabled': enabled})
    return JsonResponse({'status': 'error'}, status=400)



from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Notification
from patients.models import Patient

@login_required
def mark_notification_as_read(request, notification_id):
    """Marque une notification comme lue"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Accès réservé aux patients'}, status=403)
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.status = 'read'
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def delete_notification(request, notification_id):
    """Supprime une notification"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Accès réservé aux patients'}, status=403)
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'success'})

@login_required
def mark_all_notifications_as_read(request):
    """Marque toutes les notifications comme lues"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Accès réservé aux patients'}, status=403)
    
    Notification.objects.filter(user=request.user, status='unread').update(status='read')
    return JsonResponse({'status': 'success'})

@login_required
def delete_all_notifications(request):
    """Supprime toutes les notifications"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Accès réservé aux patients'}, status=403)
    
    Notification.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'success'})