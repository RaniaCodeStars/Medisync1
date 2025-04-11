from django import forms
from .models import Doctor

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["name", "specialty", "institution", "location"]
        widgets = {
            "location": forms.Select(choices=WILAYA_CHOICES)
        }
