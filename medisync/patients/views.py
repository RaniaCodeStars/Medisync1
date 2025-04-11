from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import MedicalHistory


# ----------------------------------------
#         HISTORIQUE MÉDICAL
# ----------------------------------------

def patient_medical_history(request):
    """
    Affiche l'historique médical du patient connecté.
    """
    patient = request.user.patient_profile  # Mise à jour pour utiliser patient_profile lié à User
    medical_history = MedicalHistory.objects.filter(patient=patient).order_by('-date')
    return render(request, 'patients/patient_medical_history.html', {
        'medical_history': medical_history
    })


def add_medical_history(request):
    """
    Permet d'ajouter une entrée à l'historique médical d'un patient.
    """
    if request.method == 'POST':
        patient = request.user.patient_profile  # Mise à jour pour utiliser patient_profile
        condition = request.POST.get('condition')
        treatment = request.POST.get('treatment')
        date = request.POST.get('date')

        MedicalHistory.objects.create(
            patient=patient,
            condition=condition,
            treatment=treatment,
            date=date
        )
        messages.success(request, "Une nouvelle entrée a été ajoutée à votre historique médical.")
        return redirect('patients:patient_medical_history')
    return render(request, 'patients/add_medical_history.html')
