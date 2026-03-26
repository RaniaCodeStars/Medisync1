from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

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
    weight = models.FloatField(blank=True, null=True, verbose_name="Poids (kg)")  # Poids en kilogrammes
    height = models.FloatField(blank=True, null=True, verbose_name="Taille (cm)")  # Taille en centimètres
    notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Patient: {self.user.email}"

    # ---------------------------
    # STATISTIQUES & GRAPHIQUES
    # ---------------------------

    @classmethod
    def get_active_stats(cls, days=30):
        """
        Calcule les statistiques d'activité des patients sur une période donnée.
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        active_patients = cls.objects.filter(
    user__appointments__status='confirmed',
    user__appointments__date__range=(start_date, end_date)
).distinct().count()


        total_patients = cls.objects.count()

        return {
            'active': active_patients,
            'total': total_patients,
            'percentage': round((active_patients / total_patients) * 100, 1) if total_patients > 0 else 0,
            'inactive': total_patients - active_patients,
            'period': days
        }

    @classmethod
    def get_activity_trend(cls, days=30):
        """
        Calcule la tendance d'activité des patients (hausse ou baisse).
        """
        current_stats = cls.get_active_stats(days)
        previous_stats = cls.get_active_stats(days * 2)

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

    @classmethod
    def get_gender_distribution(cls):
        """
        Répartition des patients selon le sexe.
        """
        data = cls.objects.values('sex').annotate(count=Count('id'))
        total = cls.objects.count()

        labels = []
        counts = []
        percentages = []

        for entry in data:
            label = dict(cls.SEX_CHOICES).get(entry['sex'], 'Inconnu')
            count = entry['count']
            percent = round((count / total) * 100, 1) if total > 0 else 0

            labels.append(label)
            counts.append(count)
            percentages.append(percent)

        return {
            'labels': labels,
            'data': counts,
            'percentages': percentages
        }

    @classmethod
    def get_creation_trend(cls, days=30):
        """
        Calcule le nombre de patients créés chaque jour sur une période donnée.
        """
        start_date = timezone.now() - timedelta(days=days)
        creations = cls.objects.filter(user__date_joined__gte=start_date) \
            .annotate(date=TruncDate('user__date_joined')) \
            .values('date') \
            .annotate(count=Count('id')) \
            .order_by('date')

        return {
            'labels': [item['date'].strftime('%Y-%m-%d') for item in creations],
            'data': [item['count'] for item in creations]
        }

    @classmethod
    def get_blood_group_distribution(cls):
        """
        Répartition des patients selon le groupe sanguin.
        """
        blood_data = cls.objects.values('blood_group').annotate(count=Count('id')).order_by('-count')
        total = cls.objects.count()

        return {
            'labels': [item['blood_group'] or 'Inconnu' for item in blood_data],
            'data': [item['count'] for item in blood_data],
            'percentages': [
                round((item['count'] / total) * 100, 1) if total > 0 else 0
                for item in blood_data
            ]
        }


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




class PatientDocument(models.Model):
    """
    Modèle pour stocker les documents médicaux du patient.
    """
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='documents_Patient/')  # Stockage des fichiers
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Date d'ajout du document
    description = models.CharField(max_length=255, blank=True, null=True)  # Optionnel : description du document
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')

    def __str__(self):
        return f"{self.patient.username} - {self.document.name}"


