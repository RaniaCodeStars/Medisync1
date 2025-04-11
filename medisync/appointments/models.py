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
