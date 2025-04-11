from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from medecins.models import Doctor
from clinics.models import Clinic

def doctor_list(request):
    """
    Affiche une liste de médecins et de cliniques en fonction des critères de recherche.
    """
    recherche = request.GET.get('recherche', '').strip()  # Rechercher par nom ou spécialité
    location = request.GET.get('location', '').strip()  # Rechercher par localisation

    # Initialisation des résultats
    doctors = Doctor.objects.all()
    clinics = Clinic.objects.all()

    # Filtrage par recherche
    if recherche:
        doctors = doctors.filter(
            Q(nom__icontains=recherche) |
            Q(prenom__icontains=recherche) |
            Q(specialty__nom__icontains=recherche) |
            Q(institution__icontains=recherche)
        )
        clinics = clinics.filter(name__icontains=recherche)

    # Filtrage par localisation
    if location:
        doctors = doctors.filter(location__iexact=location)
        clinics = clinics.filter(location__iexact=location)

    # Contexte pour le rendu
    context = {
        'doctors': doctors,
        'clinics': clinics
    }
    return render(request, 'medecins/doctor_list.html', context)


def doctors_api(request):
    """
    Renvoie une API JSON avec les informations des médecins et des cliniques.
    """
    doctors = Doctor.objects.select_related('specialty').all()
    clinics = Clinic.objects.all()

    data = {
        "doctors": [
            {
                "name": f"Dr. {doc.nom} {doc.prenom}",
                "specialty": doc.specialty.nom if doc.specialty else "Non spécifié",
                "institution": doc.institution,
                "location": doc.location,
                "latitude": doc.latitude,
                "longitude": doc.longitude,
                "experience": doc.experience
            }
            for doc in doctors
        ],
        "clinics": [
            {
                "name": clinic.name,
                "phone": clinic.phone,
                "location": clinic.location,
                "latitude": clinic.latitude,
                "longitude": clinic.longitude
            }
            for clinic in clinics
        ]
    }

    return JsonResponse(data, safe=False)
