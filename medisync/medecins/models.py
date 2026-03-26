from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone


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


#--------------------------------------------------------------------------------------------------------------------

class Commune(models.Model):
    """
    Modèle représentant une commune. Chaque commune appartient à une wilaya.
    """
    name = models.CharField(max_length=100)
    wilaya = models.CharField(max_length=100, choices=WILAYA_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.wilaya})"

#--------------------------------------------------------------------------------------------------------------------

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
    notifications = models.BooleanField(default=True)
    institution = models.CharField(max_length=255, default='Inconnu')
    location = models.CharField(max_length=255, choices=WILAYA_CHOICES, default="Alger")
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(default=36.7525)
    longitude = models.FloatField(default=3.0419)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved')],default='pending')
    created_at = models.DateTimeField(default=timezone.now )
    validation_requested_at = models.DateTimeField(null=True, blank=True,auto_now_add=True)  # Ajouter par rania
    is_archived = models.BooleanField(default=False)

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

    @classmethod
    def get_active_stats(cls, days=30):
        """
        Retourne les statistiques d'activité des médecins
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Médecins avec au moins un rendez-vous confirmé dans la période
        active_doctors = cls.objects.filter(
            appointments__status='confirmed',
            appointments__date__range=(start_date, end_date)
        ).distinct().count()
        
        total_doctors = cls.objects.count()
        
        if total_doctors > 0:
            percentage = round((active_doctors / total_doctors) * 100, 1)
        else:
            percentage = 0.0
            
        return {
            'active': active_doctors,
            'total': total_doctors,
            'percentage': percentage,
            'inactive': total_doctors - active_doctors,
            'period': days
        }

    #methode pour calculer le pourcentage des medcins
    @classmethod
    def get_activity_trend(cls, days=30):
         #Calcule l'évolution du taux d'activité
        current_stats = cls.get_active_stats(days)
        previous_stats = cls.get_active_stats(days*2)  # Période précédente
    
        if previous_stats['percentage'] > 0:
           trend = round(
            ((current_stats['percentage'] - previous_stats['percentage']) / 
             previous_stats['percentage']) * 100, 1)
        else:
            trend = 0.0
        
        return {
        'trend': trend,
        'is_increasing': trend > 0
    }
    def get_profile(self):
        return self.user.profile  # Accède au profil associé de l'utilisateur




