from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from medecins.models import Specialty
from .models import Profile
from clinics.models import Clinic
from clinics.models import  WILAYA_CHOICES
from patients.models import  Patient 

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from medecins.models import Doctor

User = get_user_model()

class DoctorSignupForm(forms.ModelForm):
    # Champs liés à l'utilisateur
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer mot de passe', widget=forms.PasswordInput)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = Doctor
        fields = [
            'nom', 'prenom', 'specialty', 'experience', 'prix',
            'institution', 'location', 'accept_online_appointments',
            'default_duration', 'minimum_delay', 'maximum_delay', 'compte_RIP'
        ]
      


    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        # Création de l'utilisateur
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
        )
        user.profile_picture = self.cleaned_data.get('profile_picture')
        user.save()

        # Création du profil
        profile = Profile.objects.create(user=user, role='MEDECIN')

        # Création du docteur
        doctor = super().save(commit=False)
        doctor.user = user
        doctor.status = 'pending'
        doctor.save()

        return user  # ou return doctor si tu préfères
    
from django import forms
from django.contrib.auth import get_user_model
from accounts.models import  Profile

User = get_user_model()

class PatientSignupForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'sex', 'blood_group', 'allergies', 'compte_RIP']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        # Crée l'utilisateur
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email']
        )
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()

        # Crée le profil avec rôle PATIENT
        Profile.objects.create(user=user, role='PATIENT')

        # Crée le patient lié
        patient = super().save(commit=False)
        patient.user = user
        if commit:
            patient.save()

        return user
# forms.py
from django import forms
from django.contrib.auth import get_user_model
from clinics.models import Clinic
from django import forms
from django.contrib.auth import get_user_model
from administrators.models import  NotificationGenerale
from django.core.exceptions import ValidationError
import json

User = get_user_model()

class ClinicSignupForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")
    
    class Meta:
        model = Clinic
        fields = ['name', 'phone', 'adresse', 'location', 'site_web', 
                 'description', 'website', 'photos', 'horaires']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'horaires': forms.Textarea(attrs={'placeholder': '{"lundi": "08:00-17:00", ...}'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas")
        
        if len(cleaned_data.get('description', '')) < 50:
            raise ValidationError("La description doit contenir au moins 50 caractères")
        
        # Validation des horaires JSON
        horaires = cleaned_data.get('horaires')
        if horaires:
            try:
                if isinstance(horaires, str):
                    json.loads(horaires)
            except json.JSONDecodeError:
                raise ValidationError({"horaires": "Format JSON invalide"})

    def save(self, commit=True):
        # Création du User
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            is_active=False  # Compte désactivé en attente de validation
        )
        
        # Création du Profile
        Profile.objects.create(
            user=user,
            role='CLINIC',
            is_verified=False
        )
        
        # Création de la Clinic
        clinic = super().save(commit=False)
        clinic.user = user
        
        # Gestion des horaires JSON
        horaires = self.cleaned_data.get('horaires')
        if horaires and isinstance(horaires, str):
            clinic.horaires = json.loads(horaires)
        
        if commit:
            clinic.save()
        
        return user

'''

class ClinicSignupForm(SignupForm):
    name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=15)
    adresse = forms.CharField(max_length=255)
    location = forms.ChoiceField(choices=WILAYA_CHOICES)
    email = forms.EmailField(required=False)
    description = forms.CharField(widget=forms.Textarea)
    photos = forms.ImageField(required=False)
    
    class Meta(SignupForm.Meta):
        fields = SignupForm.Meta.fields + (
            'name', 'phone', 'adresse', 'location', 
            'email', 'description', 'photos'
        )

class PharmacistSignupForm(SignupForm):
    pharmacy_name = forms.CharField(max_length=255)
    pharmacy_address = forms.CharField(max_length=255, required=False)
    
    class Meta(SignupForm.Meta):
        fields = SignupForm.Meta.fields + (
            'pharmacy_name', 'pharmacy_address'
        )
        '''