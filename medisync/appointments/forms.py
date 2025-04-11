from django import forms
from .models import Appointment, ConsultationReason

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialiser la liste des raisons de consultation
        self.fields['consultation_reason'].queryset = ConsultationReason.objects.none()

        if 'doctor' in self.data:
            try:
                doctor_id = int(self.data.get('doctor'))
                self.fields['consultation_reason'].queryset = ConsultationReason.objects.filter(doctor_id=doctor_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
         self.fields['consultation_reason'].queryset = self.instance.doctor.consultation_reasons.all()

from django import forms
from .models import Appointment

class ModifyAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'payment_status', 'prix', 'online_link']  # Ajout du lien de téléconsultation
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'online_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Lien de téléconsultation'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_online:  # Si le rendez-vous n'est pas en ligne
            self.fields.pop('online_link')  # Supprime le champ du lien en ligne


#'date','time' ,'consultation' ,'duration' , 


from django import forms
from .models import WeeklyAvailability, SpecificAvailability

class WeeklyAvailabilityForm(forms.ModelForm):
    class Meta:
        model = WeeklyAvailability
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

        

class SpecificAvailabilityForm(forms.ModelForm):
    class Meta:
        model = SpecificAvailability
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assure que le champ `date` utilise le format ISO pour éviter les incompatibilités
        self.fields['date'].input_formats = ['%Y-%m-%d']

class ConsultationReasonForm(forms.ModelForm):
    class Meta:
        model = ConsultationReason
        fields = ['name', 'duration', 'prix']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
