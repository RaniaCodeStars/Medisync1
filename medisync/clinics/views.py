from .forms import ClinicForm
from django.shortcuts import render, get_object_or_404
from .models import Clinic

def clinic_dashboard(request, clinic_id):
    """
    Vue du tableau de bord de la clinique
    Args:
        clinic_id: ID de la clinique passé dans l'URL
    """
    # Récupération de la clinique spécifique
    clinic = get_object_or_404(Clinic, id=clinic_id)
    
    # Statistiques à afficher (exemple)
    total_doctors = clinic.doctors.count()
    # Ajoutez d'autres statistiques selon vos besoins
    
    context = {
        'clinic': clinic,
        'clinic_id': clinic.id,
        'total_doctors': total_doctors,
        # Ajoutez d'autres variables de contexte ici
    }
    
    return render(request, 'clinics/clinic_dashboard.html', context)













def clinic_list(request):
    recherche = request.GET.get('recherche', '').strip()  # Nom de la clinique
    location = request.GET.get('location', '').strip()  # Localisation

    clinics = Clinic.objects.none()  # Aucun résultat par défaut

    # Vérifier que les deux champs sont remplis
    if recherche and location:
        clinics = Clinic.objects.filter(
            Q(name__iexact=recherche) & Q(address__iexact=location)  # Nom et localisation exacts
        )

    context = {'clinics': clinics}
    return render(request, 'medecins/doctor_list.html', context)





from django.http import JsonResponse
from .models import Clinic

def clinics_api(request):
    clinics = Clinic.objects.all()
    data = [
        {
            "name": clinic.name,
            "address": clinic.address,
            "phone": clinic.phone,
            "location": clinic.location,
            "latitude": clinic.latitude,
            "longitude": clinic.longitude
        } 
        for clinic in clinics
    ]
    return JsonResponse(data, safe=False)












from .models import ClinicDoctor  # Utiliser ClinicDoctor et non Doctor
from django.shortcuts import render, get_object_or_404
from clinics.models import Clinic,Review
from django.shortcuts import render, get_object_or_404
from .models import Clinic, Review

def clinic_profile(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    reviews = Review.objects.filter(clinic=clinic)  # Récupérer les avis
    doctors = ClinicDoctor.objects.filter(clinic=clinic)  # Récupérer les médecins
    
    context = {
        'clinic': clinic,
        'reviews': reviews,  # Ajouter les avis au contexte
        'doctors': doctors,  # Ajouter les médecins au contexte
    }
    
    return render(request, 'clinics/clinic_profile.html', context)















def edit_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        form = ClinicForm(request.POST, request.FILES, instance=clinic)
        if form.is_valid():
            form.save()
            return redirect('clinic_profile', clinic_id=clinic.id)  # Redirection après modification
    else:
        form = ClinicForm(instance=clinic)

    return render(request, 'clinics/clinic_edit.html', {'form': form, 'clinic': clinic})





from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic
from .forms import HorairesForm
import json

def edit_horaires(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        form = HorairesForm(request.POST)
        if form.is_valid():
            clinic.horaires = form.cleaned_data["horaires_json"]
            clinic.save()
            return redirect('clinic_profile', clinic_id=clinic.id)

    else:
        form = HorairesForm(initial={'horaires_json': clinic.horaires})

    # Convertir les horaires pour JavaScript
    horaires_json = json.dumps(clinic.horaires if clinic.horaires else {})

    return render(request, 'clinics/edit_horaires.html', {
        'form': form,
        'clinic': clinic,
        'horaires_json': horaires_json
    })










from django.shortcuts import render, get_object_or_404
from .models import Clinic
from .models import ClinicDoctor  # Utiliser ClinicDoctor et non Doctor

def manage_doctors(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)  # Récupérer la clinique
    doctors = clinic.doctors.all()  # Récupérer tous les médecins liés à cette clinique

    return render(request, 'clinics/manage_doctors.html', {
        'clinic': clinic,
        'doctors': doctors,
    })







from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor, Clinic
from .forms import ClinicDoctorForm

from django.shortcuts import get_object_or_404, redirect, render
from .forms import ClinicDoctorForm
from .models import Clinic, ClinicDoctor
from django.contrib import messages

def add_doctor_to_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == "POST":
        # Créer un formulaire avec les données POST et les fichiers téléchargés (images)
        form = ClinicDoctorForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Si le formulaire est valide, on ne sauvegarde pas tout de suite l'objet
            doctor = form.save(commit=False)
            doctor.clinic = clinic  # Associer le médecin à la clinique
            doctor.save()  # Sauvegarder le médecin dans la base de données

            # Afficher un message de succès
            messages.success(request, "Le médecin a été ajouté à la clinique.")

            # Rediriger vers la vue de gestion des médecins de la clinique
            return redirect('manage_doctors', clinic_id=clinic.id)
        else:
            # Si le formulaire n'est pas valide, afficher un message d'erreur
            messages.error(request, "Il y a une erreur dans le formulaire.")
    else:
        form = ClinicDoctorForm()  # Créer un formulaire vide pour l'ajout

    return render(request, 'clinics/add_doctor.html', {
        'form': form,
        'clinic': clinic,
        'editing': False,  # Indiquer qu'on est en mode ajout
    })







from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor

def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id)
    clinic_id = doctor.clinic.id  # Sauvegarde l'ID de la clinique avant suppression
    doctor.delete()
    return redirect('manage_doctors', clinic_id=clinic_id)  # Redirection vers la liste des médecins




from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor
from .forms import ClinicDoctorForm

def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id)  # Récupérer le médecin à modifier
    clinic = doctor.clinic  # Récupérer la clinique associée

    if request.method == "POST":
        form = ClinicDoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('manage_doctors', clinic_id=clinic.id)  # Retour à la liste des médecins
    else:
        form = ClinicDoctorForm(instance=doctor)  # Préremplir avec les infos du médecin

    return render(request, 'clinics/add_doctor.html', {
        'form': form,
        'clinic': clinic,
        'editing': True,  # Indiquer qu'on est en mode modification
        'doctor': doctor,  # Passer le médecin à la template
    })






















# Importe le modèle User


from django.contrib.auth.decorators import login_required
from accounts.models import User  
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic, Review

def clinic_reviews(request, clinic_id):
    """Voir tous les avis d'une clinique et permettre aux patients d'ajouter un avis."""
    clinic = get_object_or_404(Clinic, id=clinic_id)
    reviews = clinic.reviews.all()  # Récupérer tous les avis associés à la clinique

    return render(request, 'clinics/clinic_reviews.html', {'clinic': clinic, 'reviews': reviews})






from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic, Review


from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic, Review

from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic, Review
from django.contrib.auth.decorators import login_required

@login_required
def add_review(request, clinic_id):
    """Ajouter un avis à une clinique (utilisateur anonyme autorisé)."""
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Ajouter l'avis avec un utilisateur anonyme si l'utilisateur n'est pas authentifié
        user = request.user if request.user.is_authenticated else None

        if rating and comment:
            Review.objects.create(clinic=clinic, user=user, rating=rating, comment=comment)

        # Rediriger vers la page de la clinique avec les avis
        return redirect('clinic_reviews', clinic_id=clinic.id)

    return render(request, 'clinics/add_review.html', {'clinic': clinic})

@login_required
def delete_review(request, review_id):
    """Supprimer un avis (uniquement si c'est l'auteur ou un admin)."""
    review = get_object_or_404(Review, id=review_id)

    if request.user == review.user or request.user.profile.role == 'ADMIN':
        review.delete()

    return redirect('clinic_reviews', clinic_id=review.clinic.id)

@login_required
def reply_review(request, review_id):
    """Répondre à un avis (uniquement pour les médecins et les admins)."""
    review = get_object_or_404(Review, id=review_id)

    if request.user.profile.role not in ['MEDECIN', 'ADMIN']:
        return redirect('clinic_reviews', clinic_id=review.clinic.id)

    if request.method == 'POST':
        review.reply = request.POST.get('reply')
        review.save()
        return redirect('clinic_reviews', clinic_id=review.clinic.id)

    return render(request, 'clinics/reply_review.html', {'review': review})









from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic
from .forms import ClinicSettingsForm
from django.contrib.auth.decorators import login_required

@login_required
def clinic_settings(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        form = ClinicSettingsForm(request.POST, instance=clinic)
        if form.is_valid():
            form.save()
            return redirect('clinic_settings', clinic_id=clinic.id)  # Redirection après mise à jour
    else:
        form = ClinicSettingsForm(instance=clinic)

    return render(request, 'clinics/clinic_settings.html', {'form': form, 'clinic': clinic})













from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClinicDoctorForm
from .models import Clinic, ClinicDoctor

from .models import DemandeDeParticipation
from .forms import DemandeDeParticipationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DemandeDeParticipationForm
from .models import Clinic, DemandeDeParticipation

def create_clinic_doctor(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        form = DemandeDeParticipationForm(request.POST, request.FILES)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.clinic = clinic
            demande.status = 'pending'  # par exemple, 'pending' pour une demande en attente
            demande.save()
            return redirect('confirm_doctor', clinic_id=clinic.id)  # Redirige vers la page de confirmation
    else:
        form = DemandeDeParticipationForm()

    return render(request, 'clinics/create_clinic_doctor.html', {
        'form': form,
        'clinic': clinic
    })








from .forms import ClinicDoctorForm
from .models import Clinic, ClinicDoctor, DemandeDeParticipation

def confirm_doctor(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    form = ClinicDoctorForm()

    # Si POST, on crée le médecin
    if request.method == 'POST':
        form = ClinicDoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.clinic = clinic
            doctor.save()
            return redirect('confirm_doctor', clinic_id=clinic.id)

    # Toutes les demandes de participation
    demandes = DemandeDeParticipation.objects.filter(clinic=clinic)

    return render(request, 'clinics/confirm_doctor.html', {
        'clinic': clinic,
        'form': form,
        'demandes': demandes
    })






from .models import ClinicDoctor, DemandeDeParticipation, Clinic
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

@require_POST
def gerer_demande(request, clinic_id, demande_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    demande = get_object_or_404(DemandeDeParticipation, id=demande_id, clinic=clinic)

    action = request.POST.get('action')

    if action == 'confirmer':
        # Ajouter à ClinicDoctor
        ClinicDoctor.objects.create(
            clinic=clinic,
            name=demande.doctor_name,
            speciality=demande.speciality,
            profile_image=demande.profile_image
        )

    # Supprimer la demande dans les deux cas
    demande.delete()

    return redirect('confirm_doctor', clinic_id=clinic.id)











from django.shortcuts import render

def help_center(request):
    return render(request, 'clinics/help_center.html')










from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from .models import Clinic, Appointment

@login_required
def prendre_rendez_vous(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validation des données
            required_fields = ['speciality', 'time_slot', 'date']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tous les champs sont obligatoires'
                }, status=400)
            
            # Conversion de la date
            try:
                appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Format de date invalide'
                }, status=400)
            
            # Vérification de la disponibilité
            if Appointment.objects.filter(
                clinic=clinic,
                date=appointment_date,
                time_slot=data['time_slot'],
                status='CONFIRMED'
            ).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ce créneau est déjà pris'
                }, status=400)
            
            # Création du rendez-vous
            appointment = Appointment.objects.create(
                clinic=clinic,
                patient=request.user,
                speciality=data['speciality'],
                date=appointment_date,
                time_slot=data['time_slot'],
                status='CONFIRMED'
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Rendez-vous créé avec succès',
                'appointment': {
                    'id': appointment.id,
                    'speciality': appointment.speciality,
                    'date': appointment.date.strftime('%d/%m/%Y'),
                    'time_slot': appointment.time_slot,
                    'clinic': clinic.name
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    # GET request - Afficher le formulaire
    specialties = clinic.doctors.values_list('speciality', flat=True).distinct()
    return render(request, 'clinics/prendre_rendez_vous.html', {
        'clinic': clinic,
        'specialties': specialties
    })

@login_required
def annuler_rendez_vous(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    if request.method == 'POST':
        try:
            appointment.status = 'CANCELLED'
            appointment.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Rendez-vous annulé avec succès'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Méthode non autorisée'
    }, status=405)

def rendez_vous_succes(request):
    return render(request, 'clinics/rendez_vous_succes.html')