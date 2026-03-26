from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from clinics.models import Clinic
from medecins.models import Doctor
from django.conf import settings

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Utilisation de authenticate pour vérifier le mot de passe
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)  # Connexion de l'utilisateur

            # Vérifier si l'utilisateur a un profil
            if hasattr(user, 'profile'):
                role = user.profile.role
                is_verified = user.profile.is_verified  # Vérification si le profil est validé
            else:
                role = None
                is_verified = False  # Aucun profil donc non vérifié

            # Si le rôle est "MEDECIN" et qu'il n'est pas vérifié, rediriger vers un message de confirmation
            if role == 'MEDECIN' and not is_verified:
                messages.warning(request, "Votre compte est en attente de validation par un administrateur.")
                return redirect('accounts:login')  # Rediriger vers la page de login pour informer l'utilisateur

            # Redirection en fonction du rôle de l'utilisateur
            if role == 'MEDECIN':
                return redirect('accounts:dashboard_medecin')
            elif role == 'PATIENT':
                return redirect('patients:dashboard')
            elif role == 'PHARMACIEN':
                return redirect('accounts:dashboard_pharmacien')
            elif role == 'ADMIN':
                return redirect('administrators:dashboard_admin')
            elif role == 'CLINIC':
                return redirect('clinics:clinic_dashboard')
            else:
                # Si aucun rôle ou rôle non valide
                return redirect('/')

        else:
            messages.error(request, 'Email ou mot de passe incorrect.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_medecin(request):
    return render(request, 'accounts/dashboard_medcin.html')

@login_required
def dashboard_patient(request):
    return render(request, 'accounts/dashboard_patient.html')



from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import DoctorSignupForm 
from .models import Profile
from medecins.models import Doctor
from patients.models import Patient
from clinics.models import Clinic
WILAYA_CHOICES = [
    ("Alger", "Alger"),
    ("Oran", "Oran"),
    ("Constantine", "Constantine"),
    ("Annaba", "Annaba"),
    ("Tlemcen", "Tlemcen"),
]
from django.contrib import messages
from medecins.models import Specialty
#from .forms import PharmacistSignupForm

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
#from .forms import SignupForm, DoctorSignupForm, PatientSignupForm, PharmacistSignupForm, ClinicSignupForm
from .models import Profile, User
from medecins.models import Specialty, Doctor
from patients.models import Patient
from clinics.models import Clinic
from django.shortcuts import render, redirect
from django.contrib.auth import login

from .forms import *

def role_choice(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        return redirect(f'accounts:signup_{role.lower()}')
    
    return render(request, 'accounts/role_choice.html', {
        'roles': Profile.ROLE_CHOICES[1:]  # Exclure ADMIN si nécessaire
    })
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from administrators.models import NotificationGenerale
# En haut du fichier
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)

def doctor_signup_view(request):
    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                doctor = Doctor.objects.get(user=user)
                
                try:
                    admin_profile = Profile.objects.get(role='ADMIN')
                    admin_user = admin_profile.user
                    
                    NotificationGenerale.objects.create(
                        sender=user,
                        recipient=admin_user,
                        type='nouveau_compte_medecin',
                        title=f'Demande de Validation pour  Dr {doctor.nom}',
                        message=f"Nouveau médecin: {doctor.nom} ({user.email})"
                    )
                    
                    messages.success(request, "Demande envoyée à l'administrateur.")
                    return redirect('accounts:waiting_validation')  # Changé à 'accounts'
                    
                except Profile.DoesNotExist:
                    messages.error(request, "Aucun administrateur configuré")
                    return redirect('accounts:doctor_signup')  # Changé à 'accounts'
                    
            except Exception as e:
                messages.error(request, "Erreur lors de la création du compte")
                return redirect('accounts:doctor_signup')  # Changé à 'accounts'
    
    form = DoctorSignupForm()
    return render(request, 'accounts/doctor_signup.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import PatientSignupForm

def patient_signup_view(request):
    if request.method == 'POST':
        form = PatientSignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # C'est un User, pas un Patient
            print(f"Utilisateur créé: {user.email}")  # Debug
            # Vérification que le profil existe
            if hasattr(user, 'profile'):
                    print(f"Profil trouvé, rôle: {user.profile.role}")  # Debug
            else:
                    print("Aucun profil trouvé!")  # Debug
                    Profile.objects.create(user=user, role='PATIENT')  # Création de secours
                
            login(request, user)
            messages.success(request, "Bienvenue sur MediSync !")
            return redirect('accounts:dashboard_patient')
        
    else:
        form = PatientSignupForm()

    return render(request, 'accounts/patient_signup.html', {'form': form})

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.forms import ClinicSignupForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from administrators.models import NotificationGenerale
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def clinic_signup_view(request):
    if request.method == 'POST':
        form = ClinicSignupForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                
                # Notification à l'admin
                try:
                    admin_profile = Profile.objects.get(role='ADMIN')
                    NotificationGenerale.objects.create(
                        sender=user,
                        recipient=admin_profile.user,
                        type='nouveau_compte_clinic',
                        title=f'Nouvelle clinique: {form.cleaned_data["name"]}',
                        message=(
                            f"Une nouvelle clinique demande son inscription:\n"
                            f"• Nom: {form.cleaned_data['name']}\n"
                            f"• Email: {user.email}\n"
                            f"• Localisation: {form.cleaned_data.get('location', 'Non spécifiée')}\n"
                            f"• Téléphone: {form.cleaned_data['phone']}"
                        )
                    )
                except Profile.DoesNotExist:
                    logger.error("Aucun administrateur trouvé pour la notification")
                
                messages.success(request, "Votre demande a été envoyée. Vous recevrez un email de confirmation.")
                return redirect('accounts:waiting_validation')
                
            except Exception as e:
                logger.error(f"Erreur inscription clinique: {str(e)}", exc_info=True)
                messages.error(request, "Une erreur est survenue lors de l'inscription.")
                return redirect('accounts:clinic_signup')
    else:
        form = ClinicSignupForm()
    
    return render(request, 'accounts/clinic_signup.html', {'form': form})


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.shortcuts import render, redirect

@login_required
def delete_account(request):
    if request.method == 'POST':
        # Vérification du mot de passe
        password = request.POST.get('password')
        user = request.user
        
        if not user.check_password(password):
            messages.error(request, "Le mot de passe est incorrect")
            return redirect('accounts:delete_account')
            
        try:
            # Suppression du compte
            user.delete()
            # Déconnexion
            auth.logout(request)
            messages.success(request, "Votre compte a été supprimé avec succès")
            return redirect('core:home')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
    
    return render(request, 'accounts/delete_account.html')