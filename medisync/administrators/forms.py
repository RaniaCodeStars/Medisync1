from django import forms
from medecins.models import Doctor
from core.models import Notification
from patients.models import Patient
from clinics.models import Clinic, RendezVous
from .models import AdminActivityLog

from django import forms
from medecins.models import Specialty


class SpecialityForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ['nom'] 
        labels = {
            'nom': 'Nom de la spécialité',
              
        }
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le nom de la spécialité'
            }),
            
        }
from django import forms
from django.contrib.auth import get_user_model
from patients.models import Patient
from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Profile

class PatientForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput, required=False)

    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'sex', 'blood_group', 'allergies', 'compte_RIP']

    def __init__(self, *args, **kwargs):
        self.editing = kwargs.pop('editing', False)
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not self.editing or (self.editing and self.instance.user.email != email):
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.editing or (self.editing and self.instance.user.username != username):
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        if self.editing:
            # Mise à jour
            user = self.instance.user
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            if self.cleaned_data['password1']:
                user.set_password(self.cleaned_data['password1'])
        else:
            # Création
            user = User(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email']
            )
            user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            if not self.editing:
                Profile.objects.create(user=user, role='PATIENT')

        patient = super().save(commit=False)
        patient.user = user
        if commit:
            patient.save()

        return user


#clinic
from django import forms
from clinics.models import Clinic
from django.core.exceptions import ValidationError
import json
import json
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
User = get_user_model()



class ClinicSignupForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirmez le mot de passe"
    )

    class Meta:
        model = Clinic
        fields = [
            'name', 'phone', 'adresse', 'location', 'site_web',
            'description', 'website', 'photos', 'horaires'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'horaires': forms.Textarea(attrs={'placeholder': '{"lundi": "08:00-17:00", ...}'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas.")

        if len(cleaned_data.get('description', '')) < 50:
            raise ValidationError("La description doit contenir au moins 50 caractères.")

        # Valider que 'horaires' est un JSON valide
        horaires = cleaned_data.get('horaires')
        if horaires:
            try:
                if isinstance(horaires, str):
                    json.loads(horaires)
            except json.JSONDecodeError:
                raise ValidationError({"horaires": "Le format JSON des horaires est invalide."})

        return cleaned_data

    def save(self, commit=True):
        # Création de l'utilisateur
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            is_active=True  # Compte activé immédiatement
        )

        # Création du profil lié
        profile = Profile.objects.create(
            user=user,
            role='CLINIC',
            is_verified=True
        )

        # Création de la clinique
        clinic = super().save(commit=False)
        clinic.user = user

        # Traitement des horaires (JSON)
        horaires = self.cleaned_data.get('horaires')
        if horaires and isinstance(horaires, str):
            clinic.horaires = json.loads(horaires)

        if commit:
            clinic.save()

        # Envoi de l'email de confirmation
        subject = 'Votre compte Clinique Medisync est activé'
        html_message = render_to_string('administrators/clinic_approved.html', {
            'clinic': clinic,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email à la clinique : {e}")

        return user



from django import forms
from medecins.models import Doctor
User = get_user_model()

class DoctorForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirmer mot de passe', widget=forms.PasswordInput, required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = Doctor
        fields = [
            'nom', 'prenom', 'specialty', 'experience', 'prix',
            'institution', 'location', 'accept_online_appointments',
            'default_duration', 'minimum_delay', 'maximum_delay', 'compte_RIP'
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if instance and instance.user:
            self.fields['email'].initial = instance.user.email
            self.fields['username'].initial = instance.user.username
            self.fields['profile_picture'].initial = instance.user.profile_picture

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        doctor = super().save(commit=False)

        # Récupérer l'utilisateur existant
        user = doctor.user

        # Mise à jour des champs User
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            user.profile_picture = profile_picture

        password1 = self.cleaned_data.get("password1")
        if password1:
            user.set_password(password1)

        if commit:
            user.save()
            doctor.save()

        return doctor

#clinic
from django import forms
from django.forms import inlineformset_factory
from clinics.models import Clinic, ClinicDoctor

class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = '__all__'
        exclude = ['user']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'appointment_policy': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class ClinicDoctorForm(forms.ModelForm):
    class Meta:
        model = ClinicDoctor
        fields = ['name', 'speciality', 'profile_image']

ClinicDoctorFormSet = inlineformset_factory(
    Clinic,
    ClinicDoctor,
    form=ClinicDoctorForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)