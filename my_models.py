from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Vous indiquez ici que l'email est le champ de connexion principal
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Le nom d'utilisateur est requis malgré l'authentification par email

    def __str__(self):
        return self.email

class Profile(models.Model):
    ROLE_CHOICES = [
        ('MEDECIN', 'Médecin'),
        ('PATIENT', 'Patient'),
        ('ADMIN', 'Admin'),
        ('PHARMACIEN', 'Pharmacien'),
        ('CLINIC','clinic'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    is_verified = models.BooleanField(default=False)  # Indique si l'utilisateur a été vérifié
    clinic_name = models.CharField(max_length=255, blank=True, null=True)  # Optionnel, pour les médecins

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_doctor(self):
        return self.role == 'MEDECIN'

    @property
    def is_patient(self):
        return self.role == 'PATIENT'

    @property
    def is_pharmacist(self):
        return self.role == 'PHARMACIEN'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

#app administrators
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    special_access = models.BooleanField(default=False)
    dashboard_config = models.JSONField(default=dict)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin Profile - {self.user.email}"

class AdminNotification(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

class AdminActivityLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

#app appointments
from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

User = get_user_model()

class ConsultationReason(models.Model):
    """
    Motifs de consultation spécifiques à un médecin.
    """
    doctor = models.ForeignKey('medecins.Doctor', on_delete=models.CASCADE, related_name='consultation_reasons')
    name = models.CharField(max_length=100)  # Nom du motif
    duration = models.IntegerField(default=30)  # Durée en minutes
    description = models.TextField(blank=True, null=True)  # Description optionnelle
    prix = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.duration} min)"


class WeeklyAvailability(models.Model):
    """
    Disponibilités récurrentes hebdomadaires pour un médecin.
    """
    DAYS_OF_WEEK = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ]
    doctor = models.ForeignKey('medecins.Doctor', on_delete=models.CASCADE, related_name='weekly_availabilities')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)  # Jour de la semaine
    start_time = models.TimeField()  # Heure de début
    end_time = models.TimeField()  # Heure de fin
    is_emergency = models.BooleanField(default=False)  # Champ pour indiquer si le créneau est réservé aux urgences

    def clean(self):
        """
        Validation des heures de début et de fin.
        """
        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être avant l'heure de fin.")

    def __str__(self):
        return f"{self.doctor.user.email} - {self.day}: {self.start_time} à {self.end_time}"


class SpecificAvailability(models.Model):
    """
    Disponibilités ponctuelles pour une date précise.
    """
    doctor = models.ForeignKey('medecins.Doctor', on_delete=models.CASCADE, related_name='specific_availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)  # Créneau actif ou non

    def clean(self):
        # Vérifie que start_time et end_time ne sont pas None
        if not self.start_time or not self.end_time:
            raise ValidationError("L'heure de début et l'heure de fin doivent être renseignées.")

        # Vérifie que start_time est bien avant end_time
        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être avant l'heure de fin.")

    def __str__(self):
        return f"{self.doctor.user.email} - {self.date}: {self.start_time} à {self.end_time}"


from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Appointment(models.Model):
    """
    Modèle représentant un rendez-vous entre un médecin et un patient.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
    ]
    PAYMENT_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
    ]

    doctor = models.ForeignKey('medecins.Doctor', on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')   
    date = models.DateField()
    time = models.TimeField()
    consultation_reason = models.ForeignKey(
        'ConsultationReason', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True
    )  
    duration = models.IntegerField(editable=False)  # Calcul automatique
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(max_length=500, null=True, blank=True)
    prix = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    emergency_reason = models.TextField(blank=True, null=True)
    is_emergency = models.BooleanField(default=False)  # Champ pour indiquer si le créneau est réservé aux urgences

    def calculate_prix(self):
        """Version ultra-robuste avec debug"""
        prix_calcule = 0.00
        
        try:
            if self.consultation_reason and self.consultation_reason.prix:
                print("Utilisation du prix de la raison de consultation")
                prix_calcule = float(self.consultation_reason.prix)
            elif hasattr(self, 'doctor') and self.doctor.prix:
                print("Utilisation du prix par défaut du médecin")
                prix_calcule = float(self.doctor.prix)
        except Exception as e:
            print(f"Erreur calcul prix: {e}")
        
        print(f"Prix calculé: {prix_calcule}")
        return prix_calcule

    

    def get_duration(self):
        """
        Retourne la durée du rendez-vous selon le motif de consultation ou le médecin.
        """
        if self.consultation_reason:
            return self.consultation_reason.duration
        return getattr(self.doctor, 'default_duration', 30)  # Durée par défaut

    def clean(self):
        # Si le médecin a défini des motifs de consultation, le rendez-vous doit en avoir un.
        if self.doctor.consultation_reasons.exists() and not self.consultation_reason:
            raise ValidationError("Vous devez sélectionner un motif de consultation pour ce médecin.")

        # Calculer la durée du rendez-vous
        self.duration = self.get_duration()
        
        # Construire les intervalles de temps
        start_dt = datetime.combine(self.date, self.time)
        end_dt = start_dt + timedelta(minutes=self.duration)

        # Vérifier le chevauchement avec les rendez-vous existants pour ce médecin ce jour-là
        overlapping_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
        ).exclude(pk=self.pk)

        for app in overlapping_appointments:
            other_start = datetime.combine(app.date, app.time)
            other_end = other_start + timedelta(minutes=app.duration)
            # Les plages se chevauchent si start_dt < other_end et other_start < end_dt
            if start_dt < other_end and other_start < end_dt:
                raise ValidationError("Ce créneau est déjà réservé.")

        # Empêcher un médecin de prendre rendez-vous avec lui-même
        if self.doctor.user == self.patient:
            raise ValidationError("Un médecin ne peut pas prendre un rendez-vous avec lui-même.")

    def save(self, *args, **kwargs):
     # Récupérer et retirer l'argument personnalisé
     skip_prix_calculation = kwargs.pop('skip_prix_calculation', False)
    
     # Si l'argument est False, recalculer le prix
     if not skip_prix_calculation:
         self.prix = self.calculate_prix()
    
     # Appeler la méthode `save()` de la classe parente
     super().save(*args, **kwargs)

#app clinics
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
    
    

#app core
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()



class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
# Create your models here.


#app medcins
from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta


User = get_user_model()

WILAYA_CHOICES = [
    ("Alger", "Alger"),
    ("Oran", "Oran"),
    ("Constantine", "Constantine"),
    ("Annaba", "Annaba"),
    ("Tlemcen", "Tlemcen"),
]

class Specialty(models.Model):
    """
    Spécialité médicale pour les médecins.
    """
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class Doctor(models.Model):
    """
    Modèle représentant un médecin.
    """
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    limit_choices_to={'profile__role': 'MEDECIN'},
    related_name="doctor_profile"  # Ajout d'un related_name------k
    )

    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, related_name="doctors")
    experience = models.IntegerField()
    compte_RIP = models.CharField(max_length=20, blank=True, null=True)#-----k
    default_duration = models.IntegerField(default=30)
    minimum_delay = models.IntegerField(null=True, blank=True)  # Délai minimum (en jours)----k
    maximum_delay = models.IntegerField(null=True, blank=True)  # Délai maximum (en jours)----k
    accept_online_appointments = models.BooleanField(default=False)#-----k
    prix = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    institution = models.CharField(max_length=255, default='Inconnu')
    location = models.CharField(max_length=255, choices=WILAYA_CHOICES, default="Alger")
    latitude = models.FloatField(default=36.7525)
    longitude = models.FloatField(default=3.0419)

    def get_minimum_delay(self):
        # Retourne le délai minimum configuré ou une valeur par défaut (24 heures)
        return timedelta(days=self.minimum_delay if self.minimum_delay is not None else 1)

    def get_maximum_delay(self):
        # Retourne le délai maximum configuré ou une valeur par défaut (90 jours)
        return timedelta(days=self.maximum_delay if self.maximum_delay is not None else 90)

    def get_coordinates(self):
        return {
            "Alger": (36.7525, 3.0419),
            "Oran": (35.6971, -0.6337),
            "Constantine": (36.3650, 6.6147),
            "Annaba": (36.9008, 7.7564),
            "Tlemcen": (34.8828, -1.3163),
        }.get(self.location, (28.0339, 1.6596))

    def save(self, *args, **kwargs):
        self.latitude, self.longitude = self.get_coordinates()
        super().save(*args, **kwargs)

    def __str__(self):#--------k
        status = "Accepte RDV en ligne" if self.accept_online_appointments else "N'accepte pas RDV en ligne"
        return f"Dr. {self.nom} {self.prenom} - {self.specialty.nom if self.specialty else 'Non spécifié'} ({status})"
    
#app patient
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):
    """
    Modèle représentant un patient.
    """
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]

    SEX_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'profile__role': 'PATIENT'},  # Filtrer pour n'afficher que les utilisateurs avec le rôle "PATIENT"
        related_name="patient_profile"
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)  # Groupe sanguin
    allergies = models.TextField(blank=True, null=True)  # Allergies éventuelles
    nom = models.CharField(max_length=50, blank=True, null=True)  
    prenom = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    compte_RIP = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.email}"


class MedicalHistory(models.Model):
    """
    Historique médical d'un patient.
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_history'
    )
    condition = models.CharField(max_length=255)  # Maladie ou condition médicale
    treatment = models.TextField()  # Traitement ou commentaire
    date = models.DateField()  # Date associée à l'événement médical

    def __str__(self):
        return f"{self.patient.user.first_name} {self.patient.user.last_name} - {self.condition}"
