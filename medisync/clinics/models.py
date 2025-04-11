from django.db import models
from datetime import datetime


WILAYA_CHOICES = [
    ("Alger", "Alger"),
    ("Oran", "Oran"),
    ("Constantine", "Constantine"),
    ("Annaba", "Annaba"),
    ("Tlemcen", "Tlemcen"),
]

class Clinic(models.Model):
    """
    Modèle représentant une clinique.
    """
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    adresse = models.CharField(max_length=255, blank=True, null=True) 
    location = models.CharField(max_length=255, choices=WILAYA_CHOICES, default="Alger")
    site_web = models.URLField(max_length=255, blank=True, null=True) 
    email = models.EmailField(max_length=255, blank=True, null=True)
    description = models.TextField(null=True, blank=True)  # Champ obligatoire
    website = models.URLField(blank=True, null=True)
    allow_reviews = models.BooleanField(default=True)
    appointment_policy = models.TextField(blank=True, null=True)
    horaires = models.JSONField(default=dict) 
    photos = models.ImageField(upload_to='clinics/', blank=True, null=True)
    latitude = models.FloatField(default=36.7525)  # Coordonnées par défaut pour Alger
    longitude = models.FloatField(default=3.0419)  # Coordonnées par défaut pour Alger
    def clean(self):
        from django.core.exceptions import ValidationError
        if len(self.description) < 255:
            raise ValidationError("La description doit contenir au moins 255 caractères.")
    def get_coordinates(self):
        """
        Récupère les coordonnées géographiques pour la localisation sélectionnée.
        """
        coordinates = {
            "Alger": (36.7525, 3.0419),
            "Oran": (35.6971, -0.6337),
            "Constantine": (36.3650, 6.6147),
            "Annaba": (36.9008, 7.7564),
            "Tlemcen": (34.8828, -1.3163),
        }
        return coordinates.get(self.location, (28.0339, 1.6596))  # Par défaut : Centre Algérie

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour définir automatiquement les coordonnées.
        """
        self.latitude, self.longitude = self.get_coordinates()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Représentation sous forme de chaîne.
        """
        return f"{self.name} - {self.location}"






class ClinicDoctor(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='doctors/', default='default.jpg')

    def __str__(self):
        return f"{self.name} - {self.speciality}"






from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

class DeleteDoctorView(LoginRequiredMixin, View):
    def post(self, request, doctor_id):
        doctor = get_object_or_404(ClinicDoctor, id=doctor_id)
        
        if request.user.clinic != doctor.clinic:
            messages.error(request, "Action non autorisée")
            return redirect('home')
        
        doctor.delete()
        messages.success(request, "Demande supprimée")
        return redirect('doctor_requests')





from django.db import models
from django.utils import timezone
from clinics.models import Clinic
from accounts.models import User  # Vérifie que c'est bien le bon import
# models.py dans l'application `clinics`
from django.db import models
from django.utils import timezone
from clinics.models import Clinic
from accounts.models import User  # Vérifie que c'est bien le bon import

class Review(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Autoriser les utilisateurs anonymes
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    reply = models.TextField(blank=True, null=True)  # Réponse du médecin/admin

    def __str__(self):
        user_email = self.user.email if self.user else "Utilisateur inconnu"
        return f"Avis de {user_email} sur {self.clinic.name}"









from django.db import models
from django.utils import timezone

class DemandeDeParticipation(models.Model):
    clinic = models.ForeignKey('Clinic', on_delete=models.CASCADE, related_name="participations")
    
    doctor_name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to="doctor_profiles/", null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    request_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Demande de {self.doctor_name} pour {self.clinic.name}"

    class Meta:
        verbose_name = "Demande de participation"
        verbose_name_plural = "Demandes de participation"


from django.db import models
from accounts.models import User

class Appointment(models.Model):
    clinic = models.ForeignKey(
        'Clinic', 
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='patient_appointments',  # Nom unique pour éviter les conflits
        null=True
    )
    speciality = models.CharField(max_length=100)
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmé'),
        ('CANCELLED', 'Annulé'),
        ('COMPLETED', 'Terminé'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='CONFIRMED'
    )

    class Meta:
        ordering = ['date', 'time_slot']
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'

    def __str__(self):
        if self.patient:
            return f"{self.patient.email} - {self.speciality} le {self.date} à {self.time_slot}"
        return "Patient inconnu"
    
    

