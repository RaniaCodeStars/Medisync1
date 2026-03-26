from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg
from django.db.models.functions import TruncDay
from .models import Clinic, DemandeDeParticipation, RendezVous, ClinicDoctor
from django.utils.timezone import now
from datetime import date
from django.utils.timezone import localdate

@login_required
def clinic_dashboard(request):
    clinic = get_object_or_404(Clinic, user=request.user)
    today = localdate()  # ex: 2025-05-05
    today = date.today()
    total_du_jour = RendezVous.objects.count()
    max_rdv = 8
    if max_rdv == 0:
        percent = 0
    else:
        percent = int((total_du_jour / max_rdv) * 100)
    rendezvous = RendezVous.objects.filter(jour=today)
    start_of_week = today - timezone.timedelta(days=today.weekday())
    last_30_days = today - timezone.timedelta(days=30)

    # Rendez-vous - pour graphique
    rdv_stats = (
        RendezVous.objects.filter(clinic=clinic, jour__gte=last_30_days)
        .annotate(day=TruncDay('jour'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    rendezvous_dates = [entry['day'].strftime('%Y-%m-%d') for entry in rdv_stats]
    rendezvous_counts = [entry['count'] for entry in rdv_stats]

    # Statistiques générales
    total_doctors = clinic.doctors.count()
    total_reviews = clinic.review_set.count()
    average_rating = clinic.review_set.aggregate(avg=Avg('rating'))['avg'] or 0

    # Statistiques rendez-vous
    rendezvous_stats = {
        'total': RendezVous.objects.filter(clinic=clinic).count(),
        'confirmed': RendezVous.objects.filter(clinic=clinic, status='confirme').count(),
        'cancelled': RendezVous.objects.filter(clinic=clinic, status='annule').count(),
        'pending': RendezVous.objects.filter(clinic=clinic, status='en_attente').count(),
        'today': RendezVous.objects.filter(clinic=clinic, jour=today).count(),
        'this_week': RendezVous.objects.filter(clinic=clinic, date_creation__gte=start_of_week).count(),
    }

    # Statistiques des demandes de participation
    participation_stats = {
        'total': DemandeDeParticipation.objects.filter(clinic=clinic).count(),
        'pending': DemandeDeParticipation.objects.filter(clinic=clinic, status='pending').count(),
        'approved': DemandeDeParticipation.objects.filter(clinic=clinic, status='approved').count(),
        'rejected': DemandeDeParticipation.objects.filter(clinic=clinic, status='rejected').count(),
    }

    # Top 5 rendez-vous à venir
    upcoming_appointments = RendezVous.objects.filter(
        clinic=clinic, status='confirme', jour__gte=today
    ).order_by('jour', 'heure')[:5]

    # Avis récents
    recent_reviews = clinic.review_set.order_by('-created_at')[:5]

    # Liste des médecins
    doctors = ClinicDoctor.objects.filter(clinic=clinic).select_related('speciality')
    rendezvous = RendezVous.objects.filter(user=request.user)
    form = RendezVousForm(clinic=clinic) 
    context = {
        'clinic': clinic,
        'total_doctors': total_doctors,
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 1),
        'rendezvous_stats': rendezvous_stats,
        'participation_stats': participation_stats,
        'upcoming_appointments': upcoming_appointments,
        'recent_reviews': recent_reviews,
        'doctors': doctors,
        'rendezvous_dates': rendezvous_dates,
        'rendezvous_counts': rendezvous_counts,
        'rendezvous': rendezvous,
        'total_du_jour': total_du_jour,
        'max_rdv': max_rdv,
        'percent': percent,
    }

    return render(request, 'clinics/clinic_dashboard.html', context)




# core/views.py
from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')




from django.db.models import Q


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
from clinics.models import Clinic, Review,HoraireClinic
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from .forms import ReviewForm
import json  # Assurez-vous d'importer json
from collections import defaultdict
from clinics.models import HoraireTravail  # Ajouter l'import

@login_required
def clinic_profile(request):
    clinic = get_object_or_404(Clinic, user=request.user)
    reviews = Review.objects.filter(clinic=clinic).order_by('-created_at')
    review_form = ReviewForm()
    doctors = ClinicDoctor.objects.filter(clinic=clinic)

    # Récupérer les horaires des médecins
    horaires_doctors = HoraireTravail.objects.filter(doctor__clinic=clinic)
    horaires_doctors_dict = defaultdict(list)
    for horaire in horaires_doctors:
        horaires_doctors_dict[horaire.doctor.id].append({
            'jour': horaire.jour,
            'heure_debut': horaire.heure_debut.strftime('%H:%M'),
            'heure_fin': horaire.heure_fin.strftime('%H:%M'),
        })

    # Horaires de la clinique (gardez si nécessaire pour autre usage)
    horaires = HoraireClinic.objects.filter(clinic=clinic)
    horaires_dict = defaultdict(list)
    for horaire in horaires:
        if not horaire.est_ferme:
            horaires_dict[horaire.jour].append({
                'ouverture': horaire.heure_ouverture.strftime('%H:%M'),
                'fermeture': horaire.heure_fermeture.strftime('%H:%M'),
            })
        else:
            horaires_dict[horaire.jour] = []

    horaires_json = json.dumps(horaires_dict)
    horaires_doctors_json = json.dumps(horaires_doctors_dict)  # JSON pour JS

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            existing = Review.objects.filter(clinic=clinic, user=request.user).first()
            if not existing:
                review = form.save(commit=False)
                review.clinic = clinic
                review.user = request.user
                review.save()
                return redirect('clinics:clinic_profile')
    else:
        form = ReviewForm()

    context = {
        'clinic': clinic,
        'reviews': reviews,
        'doctors': doctors,
        'horaires': horaires,  # Gardez si utilisé ailleurs
        'horaires_json': horaires_json,
        'horaires_struct': dict(horaires_dict),
        'horaires_doctors_json': horaires_doctors_json,  # Ajout pour JS
        'review_form': review_form,
    }

    return render(request, 'clinics/clinic_profile.html', context)











# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ClinicForm
from .models import Clinic

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ClinicForm
from .models import Clinic

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClinicForm
from .models import Clinic
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Pour feedback utilisateur

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ClinicForm
from .models import Clinic

@login_required
def edit_clinic(request):
    clinic = get_object_or_404(Clinic, user=request.user)

    if request.method == 'POST':
        form = ClinicForm(request.POST, request.FILES, instance=clinic)
        if form.is_valid():
            form.save()
            messages.success(request, "Clinique mise à jour avec succès.")
            return redirect('clinics:clinic_profile')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ClinicForm(instance=clinic)

    return render(request, 'clinics/clinic_edit.html', {'form': form, 'clinic': clinic})













import json
from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic
from .forms import HorairesForm
import json

from django.shortcuts import render, redirect, get_object_or_404
from .models import HoraireClinic, Clinic
from .forms import HorairesForm
import json
from django.contrib.auth.decorators import login_required

@login_required
def edit_horaires(request):
    clinic = get_object_or_404(Clinic, user=request.user)


    if request.method == 'POST':
        # Si c'est une requête POST, on traite le formulaire
        form = HorairesForm(request.POST)
        if form.is_valid():
            horaires_json = form.cleaned_data["horaires_json"]
            
            # Supprimer les anciens horaires avant de les sauvegarder
            HoraireClinic.objects.filter(clinic=clinic).delete()

            for jour, horaires in horaires_json.items():
                for horaire in horaires:
                    ouverture = horaire.get("ouverture")
                    fermeture = horaire.get("fermeture")
                    if ouverture and fermeture:
                        HoraireClinic.objects.create(
                            clinic=clinic,
                            jour=jour,
                            heure_ouverture=ouverture,
                            heure_fermeture=fermeture,
                            est_ferme=False
                        )
                    else:
                        HoraireClinic.objects.create(
                            clinic=clinic,
                            jour=jour,
                            est_ferme=True
                        )

            return redirect('clinics:clinic_profile')

    else:
        # Si c'est une requête GET, on crée un formulaire avec les horaires existants
        horaires_existants = HoraireClinic.objects.filter(clinic=clinic)
        
        horaires_dict = {}
        for horaire in horaires_existants:
            if horaire.est_ferme:
                horaires_dict[horaire.jour] = []
            else:
                if horaire.jour not in horaires_dict:
                    horaires_dict[horaire.jour] = []
                horaires_dict[horaire.jour].append({
                    "ouverture": horaire.heure_ouverture.strftime('%H:%M') if horaire.heure_ouverture else '',
                    "fermeture": horaire.heure_fermeture.strftime('%H:%M') if horaire.heure_fermeture else ''
                })

        form = HorairesForm(initial={'horaires_json': horaires_dict})

    # Convertir les horaires pour JavaScript
    horaires_json = json.dumps(horaires_dict if horaires_dict else {})

    return render(request, 'clinics/edit_horaires.html', {
        'form': form,
        'clinic': clinic,
        'horaires_json': horaires_json
    })





from django.shortcuts import render, redirect, get_object_or_404
from .models import HoraireClinic, Clinic
import json
from django.contrib.auth.decorators import login_required

@login_required
def save_horaires(request):
    clinic = get_object_or_404(Clinic, user=request.user)


    if request.method == "POST":
        horaires_json = request.POST.get("horaires_json", "{}")
        horaires_dict = json.loads(horaires_json)
        
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        # Supprimer les anciens horaires avant de sauvegarder les nouveaux
        HoraireClinic.objects.filter(clinic=clinic).delete()

        for jour in jours_semaine:
            horaires = horaires_dict.get(jour)

            if horaires:
                for horaire in horaires:
                    ouverture = horaire.get("ouverture")
                    fermeture = horaire.get("fermeture")
                    
                    if ouverture and fermeture:
                        HoraireClinic.objects.create(
                            clinic=clinic,
                            jour=jour,
                            heure_ouverture=ouverture,
                            heure_fermeture=fermeture,
                            est_ferme=False
                        )
            else:
                # Si aucun horaire pour ce jour, enregistrer comme fermé
                HoraireClinic.objects.create(
                    clinic=clinic,
                    jour=jour,
                    est_ferme=True
                )

        return redirect('clinics:clinic_dashboard')
    
    return render(request, 'clinics/edit_horaires.html', {'clinic': clinic})








from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Clinic, ClinicDoctor,RendezVous

@login_required
def manage_doctors(request):
    user = request.user
    clinic = get_object_or_404(Clinic, user=user)
    doctors = clinic.doctors.all().annotate(
        appointment_count=Count('rendezvous')
    )    
    doctor_rendezvous = {}
    for doctor in doctors:
        # Récupère tous les rendez-vous associés à ce médecin
        doctor_rendezvous[doctor.id] = doctor.rendezvous.all()  # Accède à la relation inverse

    return render(request, 'clinics/manage_doctors.html', {
        'clinic': clinic,
        'doctors': doctors,
        'doctor_rendezvous': doctor_rendezvous,  # Passe les rendez-vous au template
    })
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import ClinicDoctor, Clinic

@login_required
def doctor_rendezvous(request, doctor_id):
    user = request.user  # 👈 user connecté

    # Récupérer la clinique liée à l'utilisateur
    clinic = get_object_or_404(Clinic, user=user)

    # S'assurer que le médecin appartient à cette clinique (sécurité)
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id, clinic=clinic)

    # Récupérer ses rendez-vous
    rendezvous = doctor.rendezvous.all()

    return render(request, 'clinics/doctor_rendezvous.html', {
        'user': user,
        'clinic': clinic,       # 👈 envoyer clinic au template
        'doctor': doctor,
        'rendezvous': rendezvous,
    })






from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import ClinicDoctor, Clinic
from .forms import ClinicDoctorForm

@login_required
def add_doctor_to_clinic(request):
    # Récupérer la clinique liée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)

    if request.method == "POST":
        form = ClinicDoctorForm(request.POST, request.FILES)

        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.clinic = clinic
            doctor.save()

            messages.success(request, "Le médecin a été ajouté à la clinique.")
            return redirect('clinics:manage_doctors')  # ✅ sans clinic_id
        else:
            messages.error(request, "Il y a une erreur dans le formulaire.")
    else:
        form = ClinicDoctorForm()

    return render(request, 'clinics/add_doctor.html', {
        'form': form,
        'clinic': clinic,
        'editing': False,
    })






from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor, Clinic

@login_required
def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id)
    if doctor.clinic.user == request.user:
        doctor.delete()
    else:
        return redirect('clinics:manage_doctors')  # ou autre

    return redirect('clinics:manage_doctors')  # ✅ redirection sans clinic_id




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor
from .forms import ClinicDoctorForm

@login_required
def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id)
    clinic = doctor.clinic

    # 🔐 Sécurité : vérifier que l'utilisateur est bien le propriétaire de la clinique
    if clinic.user != request.user:
        return redirect('clinics:manage_doctors')  # ou autre page d'erreur personnalisée

    if request.method == "POST":
        form = ClinicDoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('clinics:manage_doctors')  # ✅ sans clinic_id
    else:
        form = ClinicDoctorForm(instance=doctor)

    return render(request, 'clinics/add_doctor.html', {
        'form': form,
        'clinic': clinic,
        'editing': True,
        'doctor': doctor,
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

from django.shortcuts import render, redirect
from .models import Review, Clinic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# clinics/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Clinic, Review

@login_required
def add_review(request, clinic_slug):
    clinic = get_object_or_404(Clinic, slug=clinic_slug)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Validation simple
        if not rating or not comment:
            messages.error(request, "Veuillez remplir tous les champs.")
            return redirect('clinics:clinic_profile')
        
        # Créer et sauvegarder l'avis
        Review.objects.create(
            clinic=clinic,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, "Merci pour votre avis !")
        return redirect('clinics:clinic_profile')
    
    # Si méthode GET, rediriger vers la page de la clinique



@login_required
def delete_review(request, review_id):
    """Supprimer un avis (uniquement si c'est l'auteur ou un admin)."""
    review = get_object_or_404(Review, id=review_id)

    if request.user == review.user or request.user.profile.role == 'ADMIN':
        review.delete()

    return redirect('clinic_profile', clinic_id=review.clinic.id)

@login_required
def reply_review(request, review_id):
    """Répondre à un avis (uniquement pour les médecins et les admins)."""
    review = get_object_or_404(Review, id=review_id)

    if request.user.profile.role not in ['MEDECIN', 'ADMIN']:
        return redirect('clinic_profile', clinic_id=review.clinic.id)

    if request.method == 'POST':
        review.reply = request.POST.get('reply')
        review.save()
        return redirect('clinic_profile', clinic_id=review.clinic.id)

    return render(request, 'clinics/clinic_profile.html', {'review': review})









from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic
from .forms import ClinicSettingsForm
from django.contrib.auth.decorators import login_required

@login_required
def clinic_settings(request):
    # Récupérer la clinique associée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)

    if request.method == 'POST':
        form = ClinicSettingsForm(request.POST, instance=clinic)
        if form.is_valid():
            form.save()
            return redirect('clinics:clinic_settings')  # Redirection vers la même page après mise à jour
    else:
        form = ClinicSettingsForm(instance=clinic)

    return render(request, 'clinics/clinic_settings.html', {'form': form, 'clinic': clinic})











#inscrire soingnat

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClinicDoctorForm
from .models import Clinic, ClinicDoctor

from .models import DemandeDeParticipation
from .forms import DemandeDeParticipationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DemandeDeParticipationForm
from .models import Clinic, DemandeDeParticipation

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DemandeDeParticipationForm
from .models import Clinic, DemandeDeParticipation

@login_required
def create_clinic_doctor(request):
    # ➤ Récupérer la clinique associée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)

    if request.method == 'POST':
        form = DemandeDeParticipationForm(request.POST, request.FILES)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.clinic = clinic
            demande.status = 'pending'  # statut par défaut
            demande.save()
            return redirect('clinics:confirm_doctor')  # ou une autre page de ton choix
    else:
        form = DemandeDeParticipationForm()

    return render(request, 'clinics/create_clinic_doctor.html', {
        'form': form,
        'clinic': clinic
    })





#affichage demande de participation de soignant dans page inscription medcin(button confrmer de formulaire )

from .forms import ClinicDoctorForm
from .models import Clinic, ClinicDoctor, DemandeDeParticipation
from django.shortcuts import render, redirect, get_object_or_404

def confirm_doctor(request):
    # Récupérer la clinique associée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)

    form = ClinicDoctorForm()

    # Si POST, on crée le médecin
    if request.method == 'POST':
        form = ClinicDoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.clinic = clinic  # Associer la clinique de l'utilisateur
            doctor.save()
            return redirect('clinics:confirm_doctor')  # Rediriger vers la page de confirmation

    # Toutes les demandes de participation
    demandes = DemandeDeParticipation.objects.filter(clinic=clinic)

    return render(request, 'clinics/confirm_doctor.html', {
        'clinic': clinic,
        'form': form,
        'demandes': demandes
    })




from .models import ClinicDoctor, DemandeDeParticipation
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

@require_POST
def gerer_demande(request, demande_id):
    # Récupérer la clinique associée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)
    
    # Récupérer la demande de participation associée à cette clinique
    demande = get_object_or_404(DemandeDeParticipation, id=demande_id, clinic=clinic)

    # Récupérer l'action (confirmer ou refuser)
    action = request.POST.get('action')

    if action == 'confirmer':
        # Ajouter à ClinicDoctor si l'action est 'confirmer'
        ClinicDoctor.objects.create(
            clinic=clinic,
            name=demande.doctor_name,
            speciality=demande.speciality,
            profile_image=demande.profile_image
        )

    # Supprimer la demande dans tous les cas
    demande.delete()
    return redirect('clinics:confirm_doctor')











from django.shortcuts import render, get_object_or_404
from .models import Clinic

def help_center(request):
    user = request.user
    try:
        clinic = Clinic.objects.get(user=user)  # Récupère la clinique liée à l'utilisateur
    except Clinic.DoesNotExist:
        clinic = None

    return render(request, 'clinics/help_center.html', {
        'user': user,
        'clinic': clinic  # N'oubliez pas de passer la clinique au template
    })





















from django.shortcuts import render, get_object_or_404
from .models import Clinic, ClinicDoctor, HoraireClinic
from django.shortcuts import render, get_object_or_404
from .models import Clinic, ClinicDoctor, HoraireClinic

from django.shortcuts import get_object_or_404, render
from .models import Clinic, ClinicDoctor, HoraireClinic, Specialty

from django.shortcuts import get_object_or_404, render
from .models import Clinic, Specialty, HoraireClinic

def clinic_modal_info(request):
    # Récupérer la clinique associée à l'utilisateur connecté
    clinic = get_object_or_404(Clinic, user=request.user)  # Utilise 'user' au lieu de 'users'

    # Récupérer les spécialités associées à cette clinique
    specialites = Specialty.objects.filter(clinicdoctor__clinic=clinic).distinct()

    # Récupérer les horaires pour cette clinique
    horaires = HoraireClinic.objects.filter(clinic=clinic).order_by('ordre')
    doctors = ClinicDoctor.objects.all().select_related('speciality')

    # Renvoyer le HTML pour le modal
    return render(request, 'clinics/modal_form.html', {
        'clinic': clinic,
        'doctors':doctors,
        'specialites': specialites,
        'horaires': horaires
    })




#envoyer un rendez vous 

from django.shortcuts import render, get_object_or_404, redirect
from .models import Clinic, DemandeRendezVous, HoraireClinic
from django.contrib.auth.decorators import login_required

@login_required
def confirm_demande(request):
    # Récupérer toutes les cliniques associées à l'utilisateur connecté
    clinics = Clinic.objects.filter(user=request.user)

    if request.method == 'POST':
        # Récupérer la clinique sélectionnée par l'utilisateur
        clinic_id = request.POST.get('clinic')
        clinic = get_object_or_404(Clinic, id=clinic_id)

        speciality_id = request.POST.get('specialite')  # Remarque : vous devez utiliser 'specialite' ici pour le form
        jour = request.POST.get('jour')

        # Vérifier si la spécialité existe
        speciality = get_object_or_404(Specialty, id=speciality_id)

        # Vérifier si une heure est disponible pour ce jour et cette clinique
        horaire = HoraireClinic.objects.filter(clinic=clinic, jour=jour).first()

        if speciality and jour and horaire:
            # Créer ou mettre à jour la demande de rendez-vous pour l'utilisateur connecté
            demande_rdv, created = DemandeRendezVous.objects.update_or_create(
                user=request.user,
                clinic=clinic,
                speciality=speciality,  # Utilisation de speciality (et non specialite)
                jour=jour,
                defaults={'heure': horaire.heure_ouverture}  # Si la demande existe déjà, mettre à jour l'heure
            )
            # Redirection vers la page de la clinique après création de la demande
            return redirect('clinics:clinic_profile')
    
    # Si GET, ou si les informations ne sont pas valides, renvoyer le formulaire
    specialites = []
    horaires = []

    if clinics.exists():
        # Récupérer les spécialités uniques de tous les médecins associés à l'utilisateur
        specialites = Specialty.objects.all()  # Vous pouvez aussi filtrer en fonction des médecins associés à la clinique
        horaires = HoraireClinic.objects.filter(clinic=clinics.first()).order_by('ordre')

    return render(request, 'clinics/modal_form.html', {
        'clinics': clinics,
        'specialites': specialites,
        'horaires': horaires
    })






def demande_confirmation(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    return render(request, 'clinics/demande_confirmation.html', {'clinic': clinic})








#laffichage de demandes rendez vous 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import DemandeRendezVous, RendezVous

@login_required
def mes_demandes(request):
    try:
        clinic = Clinic.objects.get(user=request.user)
    except Clinic.DoesNotExist:
        clinic = None

    demandes = DemandeRendezVous.objects.filter(user=request.user)
    rendezvous = RendezVous.objects.filter(user=request.user)
    form = RendezVousForm(clinic=clinic)    # Récupérer la clinique de l'utilisateur connecté
    return render(request, 'clinics/mes_demandes.html', {
        'clinic': clinic,  # Ajout de cet objet
        'form': form,
        'demandes': demandes,
        'rendezvous': rendezvous
    })










#demandde rendez vous (tt3mer f la table rendez vous )
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import DemandeRendezVous, Clinic
from medecins.models import Specialty
from patients.models import Patient
import datetime
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import ClinicDoctor, Clinic
@login_required
def envoyer_rendez_vous(request):
    if request.method == 'POST':
        # On récupère la clinique associée à l'utilisateur
        clinic = Clinic.objects.get(user=request.user)
        doctor_id = request.POST.get('doctor')
        doctor = ClinicDoctor.objects.get(id=doctor_id)
        speciality = doctor.speciality
        
        patient = request.user
        doctor_id = request.POST.get('doctor')  # Récupérer l'ID du médecin choisi
        doctor = ClinicDoctor.objects.get(id=doctor_id)  # Récupérer le médecin sélectionné
        nom = request.POST.get("nom")
        telephone = request.POST.get("telephone")
        heure_str = request.POST.get('heure')  # ex: "14:30"
        motif = request.POST.get('motif')

        # 🔁 Convertir "Lundi" → date réelle
        jours_semaine = {
            "Lundi": 0,
            "Mardi": 1,
            "Mercredi": 2,
            "Jeudi": 3,
            "Vendredi": 4,
            "Samedi": 5,
            "Dimanche": 6,
        }

        jour_str = request.POST.get('jour').capitalize()  # "lundi" → "Lundi"
        if jour_str not in jours_semaine:
            raise ValidationError(f"Jour invalide : {jour_str}")


        today = datetime.date.today()
        delta_days = (jours_semaine[jour_str] - today.weekday()) % 7
        date_du_rendezvous = today + datetime.timedelta(days=delta_days)

        # ⏰ Convertir l'heure "HH:MM" en `datetime.time`
        try:
            heure_obj = datetime.datetime.strptime(heure_str, "%H:%M").time()
        except ValueError:
            raise ValidationError("Format d'heure invalide. Utilisez HH:MM")

        # ✅ Créer la demande
        DemandeRendezVous.objects.create(
            user=request.user,
            clinic=clinic,
            doctor=doctor,  # Enregistrer un seul médecin
            speciality=speciality,
            nom=nom,
            telephone=telephone,
            jour=date_du_rendezvous,
            heure=heure_obj,
            motif=motif,
            status='en_attente',
        )

        return redirect('clinics:confirmation_rendez_vous')

    return redirect('clinics:clinic_dashboard')






    
#confirmer demande de rendes vous  
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import DemandeRendezVous, RendezVous
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import DemandeRendezVous, RendezVous

@login_required
def confirmer_demande(request, demande_id):
    # On récupère la demande seulement si elle appartient à l'utilisateur connecté
    demande = get_object_or_404(DemandeRendezVous, id=demande_id, user=request.user)

    # On crée le rendez-vous
    RendezVous.objects.create(
        user=demande.user,
        clinic=demande.clinic,
        speciality=demande.speciality,  # corrigé ici
        nom=demande.nom,
        telephone=demande.telephone,
        motif=demande.motif,
        jour=demande.jour,
        heure=demande.heure,
        doctor=demande.doctor,  # ✅ UNE seule fois

    )

    # Supprimer la demande après confirmation
    demande.delete()

    # Rediriger vers la liste des demandes
    return redirect('clinics:mes_demandes')


#supprimer demande de rendez vous 
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import DemandeRendezVous

@login_required
def supprimer_demande(request, demande_id):
    # Récupère la demande qui appartient à l'utilisateur
    demande = get_object_or_404(DemandeRendezVous, id=demande_id, user=request.user)
    demande.delete()
    return redirect('clinics:mes_demandes')
























# rendez vous (tt3mer f la table rendez vous )
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import DemandeRendezVous, Clinic
from medecins.models import Specialty
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import RendezVous
from clinics.models import Clinic, HoraireClinic
from medecins.models import Specialty
from django.shortcuts import render, redirect, get_object_or_404
from .models import RendezVous, Clinic, HoraireClinic
from .forms import RendezVousForm
from django.contrib.auth.decorators import login_required

@login_required
def ajouter_rendez_vous(request):
    clinic_id = request.POST.get('clinic_id') or request.GET.get('clinic_id')
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.method == 'POST':
        form = RendezVousForm(request.POST, clinic=clinic)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.user = request.user
            rdv.clinic = clinic
            rdv.save()
            return redirect('clinics:mes_demandes')
    else:
        form = RendezVousForm(clinic=clinic)

    return render(request, 'clinics/mes_demandes.html', {
        'form': form,
        'clinic': clinic,
    })






from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def confirmation_rendez_vous(request):
    return render(request, 'clinics/confirmation.html', {
        'user': request.user  # tu peux maintenant accéder à user.username, user.first_name, etc. dans le template
    })















from django.shortcuts import get_object_or_404, redirect, render
from .forms import RendezVousForm  # Assure-toi que le formulaire existe

from django.shortcuts import render, get_object_or_404, redirect
from .models import RendezVous
from .forms import RendezVousForm
from django.contrib.auth.decorators import login_required

@login_required
def modifier_rendez_vous(request, rdv_id):
    rendez_vous = get_object_or_404(RendezVous, id=rdv_id, user=request.user)
    clinic = rendez_vous.clinic

    if request.method == 'POST':
        form = RendezVousForm(request.POST, instance=rendez_vous, clinic=clinic)
        if form.is_valid():
            form.save()
            return redirect('clinics:mes_demandes')  # 🔁 adapte ce nom d'URL si besoin
    else:
        form = RendezVousForm(instance=rendez_vous, clinic=clinic)

    return render(request, 'clinics/modifier_rendez_vous.html', {
        'form': form,
        'rendez_vous': rendez_vous,
    })








from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import RendezVous
@login_required
def supprimer_rendez_vous(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    rdv.delete()
    return redirect('clinics:mes_demandes')




from django.shortcuts import render
from .models import HoraireClinic, DemandeRendezVous, Clinic
import datetime
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import HoraireClinic, DemandeRendezVous, Clinic
from medecins.models import Specialty
import datetime
from datetime import timedelta
from django.contrib.auth.decorators import login_required

# Durée des consultations selon spécialité
DUREES_SPECIALITES = {
    'Cardiologue': 30,
    'Généraliste': 20,
    'Dentiste': 45,
    'Dermatologue': 25,
    # ...
}

@login_required
def afficher_horaires(request):
    clinic = Clinic.objects.get(user=request.user)
    horaires = HoraireClinic.objects.filter(clinic=clinic, est_ferme=False).order_by('ordre')
    rendez_vous = DemandeRendezVous.objects.filter(clinic=clinic)

    planning = []

    for horaire in horaires:
        heure_debut = horaire.heure_ouverture
        heure_fin = horaire.heure_fermeture

        creneaux = []

        current_time = datetime.datetime.combine(datetime.date.today(), heure_debut)

        while current_time.time() < heure_fin:
            heure_creneau = current_time.time()
            est_occupe = False

            # On cherche tous les rendez-vous de ce jour-là
            rdvs_du_jour = rendez_vous.filter(jour__week_day=((horaire.ordre % 7) + 1))

            for rdv in rdvs_du_jour:
                nom_specialite = rdv.speciality.nom  # Ex: "Cardiologue"
                duree_minutes = DUREES_SPECIALITES.get(nom_specialite, 20)  # défaut : 20 min

                debut_rdv = datetime.datetime.combine(rdv.jour, rdv.heure)
                fin_rdv = debut_rdv + timedelta(minutes=duree_minutes)

                if debut_rdv.time() <= heure_creneau < fin_rdv.time():
                    est_occupe = True
                    break

            creneaux.append({
                'heure': heure_creneau.strftime("%H:%M"),
                'status': 'Occupé' if est_occupe else 'Libre'
            })

            # On prend l’intervalle selon la spécialité la plus courte (ex: 20 min)
            current_time += timedelta(minutes=20)  # tu peux ajuster selon besoin global

        planning.append({
            'jour': horaire.jour,
            'creneaux': creneaux
        })

    return render(request, 'clinics/horaires_clinic.html', {'planning': planning})


from django.shortcuts import render, get_object_or_404, redirect
from .forms import HoraireTravailForm
from clinics.models import ClinicDoctor
from .models import HoraireTravail

def ajouter_horaire(request, doctor_id):
    doctor = get_object_or_404(ClinicDoctor, id=doctor_id)

    if request.method == 'POST':
        form = HoraireTravailForm(request.POST, doctor=doctor)
        if form.is_valid():
            horaire = form.save(commit=False)
            horaire.doctor = doctor
            horaire.save()
            return redirect('clinics:clinic_dashboard')
    else:
        form = HoraireTravailForm(doctor=doctor)

    return render(request, 'clinics/ajouter_horaire.html', {'form': form, 'doctor': doctor})

from django.shortcuts import render, get_object_or_404, redirect
from .models import ClinicDoctor, HoraireClinic
from .forms import HorairesForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import HoraireTravail
from .forms import HoraireTravailForm  # On suppose que tu as un formulaire HoraireTravailForm

def modifier_horaire(request, doctor_id, horaire_id):
    # Récupère l'horaire à partir de l'ID de l'horaire et de l'ID du médecin
    horaire = get_object_or_404(HoraireTravail, id=horaire_id, doctor_id=doctor_id)

    # Vérifie si le formulaire est soumis (en POST)
    if request.method == "POST":
        form = HoraireTravailForm(request.POST, instance=horaire)
        if form.is_valid():
            form.save()
            return redirect('clinics:manage_doctors')  # Redirige où tu veux après la modification
    else:
        # Si la méthode est GET, tu affiches le formulaire avec les données existantes
        form = HoraireTravailForm(instance=horaire)

    return render(request, 'clinics/modifier_horaire.html', {'form': form, 'horaire': horaire})















from datetime import date
from django.shortcuts import render
from .models import RendezVous

def daily_appointment_stats(request):
    today = date.today()
    count = RendezVous.objects.filter(date=today).count()
    return render(request, 'clinics/clinic_dashboard.html', {'count': count})