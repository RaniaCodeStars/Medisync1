from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

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
        if not self.doctor_id:
            # On arrête la validation si le médecin n'est pas encore défini
            return

        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être avant l'heure de fin.")

        overlapping_qs = WeeklyAvailability.objects.filter(
            doctor=self.doctor,
            day=self.day,
            is_emergency=self.is_emergency
        ).exclude(pk=self.pk)

        for other in overlapping_qs:
            if self.start_time < other.end_time and other.start_time < self.end_time:
                raise ValidationError(
                    f"Conflit avec une autre disponibilité {'d\'urgence' if self.is_emergency else 'normale'}."
                )


    def save(self, *args, **kwargs):
         self.full_clean()  # Appelle clean() avant le save
         super().save(*args, **kwargs)


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
        """
        Validation complète des disponibilités spécifiques.
        Version optimisée pour travailler avec votre formulaire existant.
        """
        # 1. Validation des heures
        if not self.start_time or not self.end_time:
            raise ValidationError("Les heures de début et de fin sont obligatoires.")

        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")

        # 2. Validation de la date
        today = timezone.now().date()
        now = timezone.now().time()

        if self.date < today:
            raise ValidationError("La date ne peut pas être dans le passé.")
    
        if self.date == today and self.end_time <= now:
            raise ValidationError("Ce créneau est déjà passé pour aujourd'hui.")

        # 3. Validation du médecin (version sécurisée)
        if not hasattr(self, 'doctor') or not self.doctor_id:
            # Ne pas lever d'exception ici pour permettre la validation initiale du formulaire
            # Le médecin sera assigné dans la vue avant le save()
            return

        # 4. Vérification des conflits (uniquement si médecin est défini)
        conflicts = SpecificAvailability.objects.filter(
          doctor_id=self.doctor_id,
            date=self.date,
            is_active=True
        ).exclude(
        Q(end_time__lte=self.start_time) | Q(start_time__gte=self.end_time)
        )

        if self.pk:
            conflicts = conflicts.exclude(pk=self.pk)

        if conflicts.exists():
            conflict = conflicts.first()
            raise ValidationError(
                f"Ce créneau chevauche une disponibilité existante "
                f"({conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')})"
            )
    
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
        ('finished', 'Terminé')
    ]
    PAYMENT_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
    ]

    doctor = models.ForeignKey('medecins.Doctor', on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', null=False)   
    date = models.DateField()
    time = models.TimeField()
    consultation_reason = models.ForeignKey(
        'ConsultationReason', 
        on_delete=models.SET_NULL, 
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
        # Si le rendez-vous n'est pas une urgence et que le médecin a des motifs,
        # alors un motif doit être sélectionné
        if not self.is_emergency and self.doctor.consultation_reasons.exists() and not self.consultation_reason:
            raise ValidationError("Vous devez sélectionner un motif de consultation pour ce médecin.")

        # Déterminer la durée selon le type de rendez-vous
        if self.is_emergency:
            self.duration = getattr(self.doctor, 'default_duration', 30)
        else:
            self.duration = self.get_duration()

        # Construire les intervalles de temps
        start_dt = datetime.combine(self.date, self.time)
        end_dt = start_dt + timedelta(minutes=self.duration)

        # Vérifier le chevauchement avec d'autres rendez-vous
        overlapping_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
        ).exclude(status="cancelled").exclude(pk=self.pk)

        for app in overlapping_appointments:
            other_start = datetime.combine(app.date, app.time)
            other_end = other_start + timedelta(minutes=app.duration)
            if start_dt < other_end and other_start < end_dt:
                raise ValidationError("Ce créneau est déjà réservé.")

        # Empêcher un médecin de prendre rendez-vous avec lui-même
        if self.doctor.user == self.patient:
            raise ValidationError("Un médecin ne peut pas prendre un rendez-vous avec lui-même.")


    def save(self, *args, **kwargs):
        skip_prix_calculation = kwargs.pop('skip_prix_calculation', False)

        if not skip_prix_calculation:
            if self.is_emergency:
                self.prix = float(self.doctor.prix or 0.00)
                self.duration = getattr(self.doctor, 'default_duration', 30)
            else:
                self.prix = self.calculate_prix()
                self.duration = self.get_duration()

        super().save(*args, **kwargs)

    @classmethod
    def get_appointment_stats(cls, days=30):
   
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
    
     # Rendez-vous de la période actuelle avec annotation des counts
        status_counts = cls.objects.filter(
             date__range=(start_date, end_date)
             ).values('status').annotate(count=Count('id')).order_by('status')
    
     # Conversion en dictionnaire
        status_dict = {item['status']: item['count'] for item in status_counts}
    
     # Valeurs par défaut si aucun RDV trouvé
        confirmed = status_dict.get('confirmed', 0)
        pending = status_dict.get('pending', 0)
        cancelled = status_dict.get('cancelled', 0)
        total = confirmed + pending + cancelled
    
     # Calcul des pourcentages (en évitant la division par zéro)
        try:
            confirmed_pct = round((confirmed / total) * 100, 1)
            pending_pct = round((pending / total) * 100, 1)
            cancelled_pct = round((cancelled / total) * 100, 1)
        except ZeroDivisionError:
            confirmed_pct = pending_pct = cancelled_pct = 0.0
    
     # Calcul de la tendance
        previous_start = start_date - timedelta(days=days)
        previous_count = cls.objects.filter(
            date__range=(previous_start, start_date)
        ).count()
    
        try:
            trend = round(((total - previous_count) / previous_count) * 100, 1)
        except ZeroDivisionError:
            trend = 0.0
    
        return {
        'total': total,
        'confirmed': confirmed,
        'pending': pending,
        'cancelled': cancelled,
        'confirmed_pct': confirmed_pct,
        'pending_pct': pending_pct,
        'cancelled_pct': cancelled_pct,
        'trend': trend,
        'is_increasing': trend > 0,
        'period': days
    }


