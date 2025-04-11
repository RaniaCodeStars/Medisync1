from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

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
                return redirect('accounts:dashboard_patient')
            elif role == 'PHARMACIEN':
                return redirect('accounts:dashboard_pharmacien')
            elif role == 'ADMIN':
                return redirect('accounts:dashboard_admin')
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

@login_required
def dashboard_admin(request):
    return render(request, 'accounts/dashboard_admin.html')

@login_required
def dashboard_pharmacien(request):
    return render(request, 'dashboards/pharmacien.html')

from .forms import SignupForm
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # Création de l'utilisateur
            role = request.POST['role']

            # Créer ou obtenir le profil de l'utilisateur
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role

            if role == 'MEDECIN':
                profile.is_verified = False  # L'utilisateur médecin est en attente de validation
            profile.save()

            if role =='PATIENT':
                profile.is_verified = True
            profile.save()
            if role =='ADMIN':
                profile.is_verified = True
            profile.save()
            # Connexion automatique après l'inscription
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # Redirection selon le rôle
            if role == 'MEDECIN':
                return redirect('accounts:dashboard_medecin')
            elif role == 'PATIENT':
                return redirect('accounts:dashboard_patient')
            elif role == 'PHARMACIEN':
                return redirect('accounts:dashboard_pharmacien')
            elif role == 'ADMIN':
                return redirect('accounts:dashboard_admin')

    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def approve_medecin(request):
    if request.user.profile.role == 'ADMIN':  # Vérifie si l'utilisateur est un admin
        if request.method == 'POST':
            user_id = request.POST['user_id']
            try:
                profile = Profile.objects.get(user_id=user_id, role='MEDECIN')
                profile.is_verified = True  # Valider le médecin
                profile.save()
                messages.success(request, f"Le médecin {profile.user.username} a été validé avec succès.")
                return redirect('accounts:dashboard_admin')
            except Profile.DoesNotExist:
                messages.error(request, "Le médecin n'a pas été trouvé.")
        # Affiche tous les médecins en attente de validation
        medecins_en_attente = Profile.objects.filter(role='MEDECIN', is_verified=False)
        return render(request, 'accounts/approve_medecins.html', {'medecins_en_attente': medecins_en_attente})
    else:
        return redirect('accounts:login')  # Si l'utilisateur n'est pas admin

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()  # Supprime l'utilisateur
        return redirect('home')  # Redirige après suppression