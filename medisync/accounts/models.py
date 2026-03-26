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

from django.db import models

from django.utils.timezone import now

class NotificationAdmin(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    sujet = models.CharField(max_length=255)
    message = models.TextField()
    date_envoye = models.DateTimeField(default=now)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification pour {self.User.prenom} {self.User.nom} - {self.sujet}"

