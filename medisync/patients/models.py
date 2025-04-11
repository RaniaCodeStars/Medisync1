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
