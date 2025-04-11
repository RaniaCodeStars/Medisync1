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