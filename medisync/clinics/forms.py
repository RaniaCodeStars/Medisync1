from django import forms
from .models import Clinic

# forms.py
from django import forms
from .models import Clinic

from django import forms
from .models import Clinic

from django import forms
from .models import Clinic

class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'phone', 'adresse', 'location', 'site_web', 'description', 'photos']

        
        
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

from django import forms
from django.utils.safestring import mark_safe
from .models import Clinic

class ClinicSettingsForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = [
            'name', 'phone', 'adresse', 'location',
            'site_web', 'description', 'photos'
        ]  # 🔴 PAS de "email" ici
        labels = {
            'name': mark_safe('<i class="material-icons">person</i> Nom'),
            'phone': mark_safe('<i class="material-icons">phone</i> Téléphone'),
            'adresse': mark_safe('<i class="material-icons">place</i> Adresse'),
            'location': mark_safe('<i class="material-icons">location_on</i> Wilaya'),
            'site_web': mark_safe('<i class="material-icons">language</i> Site web'),
            'description': mark_safe('<i class="material-icons">description</i> Description'),
            'photos': mark_safe('<i class="material-icons">photo_camera</i> Photos'),
        }


from django import forms
from .models import ClinicDoctor

from django import forms
from .models import ClinicDoctor
from medecins.models import Specialty  # Assurez-vous d'importer le modèle Specialty

from django import forms
from .models import ClinicDoctor

class ClinicDoctorForm(forms.ModelForm):
    class Meta:
        model = ClinicDoctor
        fields = ['name', 'speciality', 'profile_image', 'email', 'consultation_fee', 'years_of_experience', 'telephone', 'biographie',  'disponible', ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du médecin'}),
            'speciality': forms.Select(attrs={'class': 'form-control'}),  # Utilisation de Select pour un champ ForeignKey
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email du médecin'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Frais de consultation'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Années d\'expérience'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'biographie': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Biographie du médecin', 'rows': 4}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }





from django import forms
from .models import DemandeDeParticipation

class DemandeDeParticipationForm(forms.ModelForm):
    class Meta:
        model = DemandeDeParticipation
        fields = [
            'doctor_name',
            'speciality',
            'profile_image',
            'email',
            'years_of_experience',
            'telephone',
            'biographie',
            'disponible',
            'notes',
            'certificat'
        ]

    def clean_speciality(self):
        speciality = self.cleaned_data.get('speciality')
        if not speciality:
            raise forms.ValidationError("La spécialité est obligatoire.")
        return speciality






# forms.py
from django import forms
from .models import DemandeRendezVous, Specialty, ClinicDoctor
from datetime import time, timedelta

class DemandeRendezVousForm(forms.ModelForm):
    class Meta:
        model = DemandeRendezVous
        fields = ['speciality', 'doctor', 'nom', 'telephone', 'jour', 'heure', 'motif']

    def __init__(self, *args, **kwargs):
        clinic = kwargs.pop('clinic', None)
        super().__init__(*args, **kwargs)
        
        # Filtre les médecins par clinique si spécifiée
        if clinic:
            self.fields['doctor'].queryset = ClinicDoctor.objects.filter(clinic=clinic)
        
        # Configuration des widgets
        self.fields['speciality'].widget.attrs.update({
            'class': 'form-control',
            'required': True,
            'onchange': 'filterDoctors()'
        })
        self.fields['doctor'].widget.attrs.update({
            'class': 'form-control',
            'required': True,
            'onchange': 'updateAvailableDays()'
        })
        self.fields['jour'].widget.attrs.update({
            'class': 'form-control',
            'required': True,
            'onchange': 'updateTimeSlots()'
        })
        self.fields['heure'].widget = forms.Select(choices=[])
        self.fields['heure'].widget.attrs.update({
            'class': 'form-control',
            'required': True
        })

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        jour = cleaned_data.get('jour')
        heure = cleaned_data.get('heure')
        
        if doctor and jour and heure:
            # Vérifie que l'heure est dans les horaires du médecin
            horaire = doctor.horaires.filter(jour=jour.lower()).first()
            if horaire:
                heure_time = time.fromisoformat(heure)
                if not (horaire.heure_debut <= heure_time <= horaire.heure_fin):
                    raise forms.ValidationError(
                        f"Le médecin n'est pas disponible à cette heure. "
                        f"Heures de travail: {horaire.heure_debut} - {horaire.heure_fin}"
                    )
        return cleaned_data


#prendre rendez vous et modifer rendez vous
from django import forms
from clinics.models import HoraireClinic, Clinic
from medecins.models import Specialty
from .models import RendezVous
from datetime import datetime, timedelta

class RendezVousForm(forms.ModelForm):
    speciality = forms.ModelChoiceField(
        queryset=Specialty.objects.none(),
        label="Spécialité",
        empty_label="Sélectionnez une spécialité",
        widget=forms.Select(attrs={'required': True})
    )
    
    jour = forms.ChoiceField(
        choices=[],  # سيتم ملؤها ديناميكيا
        label="Jour",
        widget=forms.Select(attrs={'required': True})
    )

    heure = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'required': True})
    )

    class Meta:
        model = RendezVous
        fields = ['speciality', 'doctor', 'nom', 'telephone', 'jour', 'heure', 'motif']
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3, 'required': True}),
            'nom': forms.TextInput(attrs={'required': True}),
            'telephone': forms.TextInput(attrs={'required': True, 'pattern': '^0[5-7][0-9]{8}$'}),
        }

    def __init__(self, *args, **kwargs):
        clinic = kwargs.pop('clinic', None)
        super().__init__(*args, **kwargs)

        if clinic:
            self.fields['speciality'].queryset = Specialty.objects.filter(clinicdoctor__clinic=clinic).distinct()

            # جلب الأيام المتاحة مع التواريخ
            horaires = HoraireClinic.objects.filter(clinic=clinic)
            today = datetime.today()
            jours_order = {
                'Lundi': 1, 'Mardi': 2, 'Mercredi': 3, 'Jeudi': 4,
                'Vendredi': 5, 'Samedi': 6, 'Dimanche': 7
            }
            self.fields['doctor'] = forms.ModelChoiceField(
                queryset=ClinicDoctor.objects.filter(clinic=clinic) if clinic else ClinicDoctor.objects.none(),
                required=False,
                label="Docteur",
                empty_label="Choisir un docteur",
                widget=forms.Select(attrs={'class': 'form-control'})
                )
            jour_choices = []

            for horaire in horaires:
                if not horaire.est_ferme:
                    # احسب تاريخ أقرب يوم مطابق
                    jour_name = horaire.jour
                    days_ahead = (jours_order[jour_name] - today.weekday() - 1) % 7
                    if days_ahead <= 0:
                        days_ahead += 7  # لو اليوم مر، نروح للأسبوع الجاي
                    target_date = today + timedelta(days=days_ahead)
                    jour_choices.append((
                        target_date.strftime('%Y-%m-%d'),  # القيمة هي التاريخ
                        f"{jour_name} ({horaire.heure_ouverture.strftime('%H:%M')} - {horaire.heure_fermeture.strftime('%H:%M')})"  # العرض
                    ))

            self.fields['jour'].choices = jour_choices

    def clean_jour(self):
        jour = self.cleaned_data['jour']
        # تحويل القيمة (التاريخ) لتاريخ Python
        try:
            return datetime.strptime(jour, '%Y-%m-%d').date()
        except ValueError:
            raise forms.ValidationError("Format de date invalide. Veuillez sélectionner un jour valide.")
        
        
        
        
        
        
        
from django import forms
from clinics.models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)])
        }










from django import forms
from .models import HoraireTravail
from clinics.models import HoraireClinic

class HoraireTravailForm(forms.ModelForm):
    jour = forms.ChoiceField(choices=[
        ("lundi", "Lundi"),
        ("mardi", "Mardi"),
        ("mercredi", "Mercredi"),
        ("jeudi", "Jeudi"),
        ("vendredi", "Vendredi"),
        ("samedi", "Samedi"),
        ("dimanche", "Dimanche"),
    ])

    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)

        if self.doctor:
            jours_ouverts = HoraireClinic.objects.filter(
                clinic=self.doctor.clinic,
                est_ferme=False
            ).values_list('jour', flat=True)
            jours_ouverts = [j.lower() for j in jours_ouverts]

            self.fields['jour'].choices = [
                (val, label) for val, label in self.fields['jour'].choices if val in jours_ouverts
            ]

    class Meta:
        model = HoraireTravail
        fields = ['jour', 'heure_debut', 'heure_fin']
