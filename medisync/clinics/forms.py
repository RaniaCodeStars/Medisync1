from django import forms
from .models import Clinic

# forms.py
from django import forms
from .models import Clinic

class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'phone', 'adresse', 'location', 'site_web', 'email', 'description', 'photos']
        horaires = forms.CharField(widget=forms.HiddenInput())
        
        
        
        
from django import forms
import json

class HorairesForm(forms.Form):
    jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    horaires_json = forms.CharField(widget=forms.HiddenInput(), required=False)  # Stocker les horaires sous forme JSON

    def clean_horaires_json(self):
        data = self.cleaned_data["horaires_json"]
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}













from django import forms
from .models import Clinic
from django.utils.safestring import mark_safe

class ClinicSettingsForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'phone', 'email']
        labels = {
            'name': mark_safe('<i class="material-icons">person</i> Nom'),
            'phone': mark_safe('<i class="material-icons">phone</i> Téléphone'),
            'email': mark_safe('<i class="material-icons">email</i> Email'),
        }




from django import forms
from .models import ClinicDoctor

class ClinicDoctorForm(forms.ModelForm):
    class Meta:
        model = ClinicDoctor
        fields = ['name', 'speciality', 'profile_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du médecin'}),
            'speciality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Spécialité'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

from django import forms
from .models import DemandeDeParticipation

class DemandeDeParticipationForm(forms.ModelForm):
    class Meta:
        model = DemandeDeParticipation
        fields = ['doctor_name', 'speciality', 'profile_image', 'notes']  # Ajoute les champs que tu souhaites inclure

    # Si tu veux personnaliser des validations ou des widgets, tu peux le faire ici
    def clean_speciality(self):
        speciality = self.cleaned_data.get('speciality')
        if not speciality:
            raise forms.ValidationError("La spécialité est obligatoire.")
        return speciality
