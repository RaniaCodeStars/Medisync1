from django.db import models
from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.db import models
from django.utils.text import slugify
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import itertools

WILAYA_CHOICES = [
    ("Alger", "Alger"),
    ("Oran", "Oran"),
    ("Constantine", "Constantine"),
    ("Annaba", "Annaba"),
    ("Tlemcen", "Tlemcen"),
]
STATUS_CHOICES = [
    ('pending', 'En attente'),
    ('approved', 'Approuvée'),
    ('rejected', 'Rejetée')
]
User = get_user_model()

class Clinic(models.Model):
    """
    Modèle représentant une clinique.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'profile__role': 'CLINIC'},  # Exemple de filtre pour un utilisateur ayant un rôle 'ADMIN'
        related_name="clinic_profile",  # Permet de récupérer la clinique via l'utilisateur
         null=True
        )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    adresse = models.CharField(max_length=255, blank=True, null=True) 
    location = models.CharField(max_length=255, choices=WILAYA_CHOICES, default="Alger")
    site_web = models.URLField(max_length=255, blank=True, null=True) 
    email = models.EmailField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=255,null=True, blank=True)  # Champ obligatoire
    website = models.URLField(blank=True, null=True)
    allow_reviews = models.BooleanField(default=True)
    appointment_policy = models.TextField(blank=True, null=True)
    horaires = models.JSONField(default=dict) 
    photos = models.ImageField(upload_to='clinics/', blank=True, null=True)
    latitude = models.FloatField(default=36.7525)  # Coordonnées par défaut pour Alger
    longitude = models.FloatField(default=3.0419)  # Coordonnées par défaut pour Alger
    slug = models.SlugField(max_length=255, unique=True , null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    class Meta:
        db_table = "clinic"
    
  
    def generate_unique_slug(self):
        slug = slugify(self.name)
        unique_slug = slug
        for i in itertools.count(1):
            if not Clinic.objects.filter(slug=unique_slug).exists():
                break
            unique_slug = f"{slug}-{i}"
        return unique_slug
    
    
    def clean(self):
        
        if self.description and len(self.description) < 50:
            raise ValidationError("La description doit contenir au moins 50 caractères.")
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
     if not self.slug:
        self.slug = self.generate_unique_slug()
     self.latitude, self.longitude = self.get_coordinates()
     super().save(*args, **kwargs)

    def __str__(self):
        """
        Représentation sous forme de chaîne.
        """
        return f"{self.name} - {self.location}"



from medecins.models import Specialty
class ClinicDoctor(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    speciality = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField(upload_to='doctors/', default='default.jpg')
    email = models.EmailField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    biographie = models.TextField(blank=True, null=True)
    disponible = models.BooleanField(default=True)

    # Ajout du related_name pour 'rendezvous'
    def __str__(self):
        return f"{self.name} - {self.speciality}"







from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
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
    speciality = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField(upload_to="doctor_profiles/", null=True, blank=True)

    # ✅ Champs ajoutés depuis ClinicDoctor
    email = models.EmailField(blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    biographie = models.TextField(blank=True, null=True)
    certificat = models.FileField(upload_to="certificats_medecins/", null=True, blank=True)
    disponible = models.BooleanField(default=True)
    

    # ✅ Champs de suivi de la demande
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
from django.db import models
from datetime import date
from datetime import datetime
from django.shortcuts import get_object_or_404

class HoraireClinic(models.Model):
    JOURS_SEMAINE = [
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche')
    ]
    
    ORDRE_JOURS = {
        'Lundi': 1,
        'Mardi': 2,
        'Mercredi': 3,
        'Jeudi': 4,
        'Vendredi': 5,
        'Samedi': 6,
        'Dimanche': 7
    }
    
    clinic = models.ForeignKey('Clinic', on_delete=models.CASCADE, related_name='horaires_clinic')
    jour = models.CharField(max_length=10, choices=JOURS_SEMAINE)
    date = models.DateField(null=True, blank=True)  # Le champ de date que tu as déjà ajouté
    heure_ouverture = models.TimeField(null=True, blank=True)
    heure_fermeture = models.TimeField(null=True, blank=True)
    est_ferme = models.BooleanField(default=False)
    ordre = models.PositiveSmallIntegerField(editable=False, null=True)
    
    class Meta:
        ordering = ['ordre']
        verbose_name = "Horaire Clinique"
        verbose_name_plural = "Horaires Clinique"
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement l'ordre lors de la sauvegarde"""
        self.ordre = self.ORDRE_JOURS.get(self.jour, 99)
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.est_ferme:
            return f"{self.jour} | Fermé"
        if self.date:
            return f"{self.jour} ({self.date.strftime('%d/%m/%Y')}) | {self.heure_ouverture.strftime('%H:%M')} - {self.heure_fermeture.strftime('%H:%M')}"
        return f"{self.jour} | {self.heure_ouverture.strftime('%H:%M')} - {self.heure_fermeture.strftime('%H:%M')}"


from django.db import models
from django.conf import settings
from clinics.models import Clinic  # Assure-toi que le chemin est correct
from clinics.models import ClinicDoctor
from django.shortcuts import get_object_or_404
class DemandeRendezVous(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('refusee', 'Refusée'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    speciality = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    nom = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)  # ➕ téléphone
    jour = models.DateField()
    heure = models.TimeField()
    motif = models.TextField(blank=True, null=True)  # ➕ motif
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')  # ➕ statut
    doctor = models.ForeignKey(ClinicDoctor,on_delete=models.SET_NULL,null=True,blank=True,related_name="rendezvous_confirmes" )
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Demande de {self.nom} ({self.speciality}) à {self.clinic.name}"





from django.db import models
from django.contrib.auth import get_user_model
from clinics.models import Clinic
from clinics.models import ClinicDoctor

User = get_user_model()

class RendezVous(models.Model):
    JOURS_SEMAINE = [
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rendezvous")
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="rendezvous")
    speciality = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    nom = models.CharField(max_length=100, blank=True, null=True)
    doctor = models.ForeignKey(ClinicDoctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='rendezvous')
    jour = models.DateField()
    heure = models.TimeField()
    date_creation = models.DateTimeField(auto_now_add=True)
    motif = models.TextField(blank=True, null=True)  # Motif de rendez-vous
    telephone = models.CharField(max_length=15, blank=True, null=True)  # Numéro de téléphone
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')  # Statut du rendez-vous

    def __str__(self):
        return f"{self.user.username} - {self.speciality} ({self.jour} à {self.heure})"





from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from clinics.models import ClinicDoctor

class HoraireTravail(models.Model):
    doctor = models.ForeignKey(ClinicDoctor, on_delete=models.CASCADE, related_name='horaires')
    jour = models.CharField(max_length=10, choices=[
        ("lundi", "Lundi"),
        ("mardi", "Mardi"),
        ("mercredi", "Mercredi"),
        ("jeudi", "Jeudi"),
        ("vendredi", "Vendredi"),
        ("samedi", "Samedi"),
        ("dimanche", "Dimanche"),
    ])
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    @property
    def creneaux_disponibles(self):
        """Génère les créneaux disponibles pour cet horaire"""
        creneaux = []
        current_time = self.heure_debut
        while current_time < self.heure_fin:
            creneaux.append(current_time.strftime('%H:%M'))
            # Ajouter 30 minutes pour le prochain créneau
            current_time = (datetime.combine(datetime.today(), current_time) + 
                          timedelta(minutes=30)).time()
        return creneaux

    @classmethod
    def get_horaires_par_medecin(cls, doctor_id):
        """Récupère les horaires groupés par jour pour un médecin"""
        return {
            horaire.jour: horaire 
            for horaire in cls.objects.filter(doctor_id=doctor_id)
        }

    def clean(self):
        if self.heure_debut and self.heure_fin:
            if self.heure_debut >= self.heure_fin:
                raise ValidationError(_("L'heure de début doit être avant l'heure de fin."))

        if self.doctor_id:
            if HoraireTravail.objects.filter(doctor=self.doctor, jour=self.jour).exclude(id=self.id).exists():
                raise ValidationError(_("Un horaire existe déjà pour ce jour."))

    def __str__(self):
        try:
            return f"{self.doctor.name} - {self.jour} de {self.heure_debut} à {self.heure_fin}"
        except:
            return "HoraireTravail (incomplet)"
