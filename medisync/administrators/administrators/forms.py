from django import forms
from .models import Doctor, Patient, Appointment, Speciality, Notification

class DoctorApprovalForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['address', 'phone', 'date_of_birth', 'blood_group']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date_time', 'reason', 'status']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class SpecialityForm(forms.ModelForm):
    class Meta:
        model = Speciality
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message', 'notification_type']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
        }