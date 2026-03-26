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



from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
'''
 # Pour les médecins
        ('demande_rdv', 'Demande de rendez-vous'),
        ('modification_rdv', 'Modification de rendez-vous'),
        ('validation_medecin', 'Validation de médecin'),
        ('inscription_medecin', 'Nouvelle inscription médecin'),

        # Pour les patients
        ('confirmation_rdv', 'Confirmation de rendez-vous'),
        ('annulation_rdv', 'Annulation de rendez-vous'),
        ('reponse_medecin', 'Réponse du médecin'),

'''

User = get_user_model()

class NotificationGenerale(models.Model):
    TYPE_CHOICES = [
       
        # Pour l’admin
        ('probleme_signale', 'Problème signalé'),

        ('nouveau_compte_medecin', 'Nouvelle demande de compte'),
        ('nouveau_compte_clinic', 'Nouvelle demande de compte'),
        ('validation_compte_clinic','Validation de clinic'),
        ('validation_compte_medecin', 'Validation de médecin'),
        ('compte_valide', 'Compte validé'),

       
    ]

    sender = models.ForeignKey(
        User, related_name='notifications_envoyees',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    recipient = models.ForeignKey(
        User, related_name='notifications_recues',
        on_delete=models.CASCADE
    )

    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='autre')
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.recipient.username}"


class AdminActivityLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ICON_CHOICES = [
        ('user-md', 'Médecin'),
        ('users', 'Patient'),
        ('calendar-check', 'Rendez-vous'),
        ('exclamation-triangle', 'Problème'),
        ('check-circle', 'Validation'),
    ]
    icon = models.CharField(max_length=20, choices=ICON_CHOICES ,default='Patient')
    class Meta:
        ordering = ['-timestamp']



class ReportedIssue(models.Model):
    class IssueStatus(models.TextChoices):
        OPEN = 'open', 'Ouvert'
        IN_PROGRESS = 'in_progress', 'En cours'
        RESOLVED = 'resolved', 'Résolu'
        REJECTED = 'rejected', 'Rejeté'
    
    class PriorityLevel(models.TextChoices):
        LOW = 'low', 'Faible'
        MEDIUM = 'medium', 'Moyen'
        HIGH = 'high', 'Élevé'
        CRITICAL = 'critical', 'Critique'

    # Relations principales
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_issues',
        verbose_name='Utilisateur qui signale'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues',
        verbose_name='Assigné à'
    )
    
    # Champs de description
    title = models.CharField(max_length=200, verbose_name='Titre')
    description = models.TextField(verbose_name='Description')
    
    # Métadonnées
    status = models.CharField(
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.OPEN,
        verbose_name='Statut'
    )
    priority = models.CharField(
        max_length=20,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIUM,
        verbose_name='Priorité'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière mise à jour')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de résolution')
    
    # Relations complémentaires (optionnelles)
    related_appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues',
        verbose_name='Rendez-vous concerné'
    )
    
    category = models.ForeignKey(
        'IssueCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues',
        verbose_name='Catégorie'
    )

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
        # Dans ReportedIssue
    def get_status_history(self):
      """Retourne l'historique des changements de statut"""
      return self.updates.exclude(status_change__isnull=True).order_by('created_at')

    def get_time_to_resolution(self):
         """Calcule le temps de résolution en heures"""
         if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
         return None

#
class IssueCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    default_priority = models.CharField(
        max_length=20,
        choices=ReportedIssue.PriorityLevel.choices,
        default=ReportedIssue.PriorityLevel.MEDIUM,
        verbose_name='Priorité par défaut'
    )
    
    class Meta:
        verbose_name = 'Catégorie de problème'
        verbose_name_plural = 'Catégories de problèmes'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_issue_stats(self):
     """Statistiques pour cette catégorie"""
     return {
        'total': self.issues.count(),
        'resolved': self.issues.filter(status=ReportedIssue.IssueStatus.RESOLVED).count(),
        'avg_resolution_time': self.issues.aggregate(
            avg_time=Avg('resolved_at' - 'created_at')
        )['avg_time']
    }
    
    
class IssueUpdate(models.Model):
    issue = models.ForeignKey(
        ReportedIssue,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name='Problème'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='issue_updates',
        verbose_name='Auteur'
    )
    
    comment = models.TextField(verbose_name='Commentaire')
    status_change = models.CharField(
        max_length=20,
        choices=ReportedIssue.IssueStatus.choices,
        null=True,
        blank=True,
        verbose_name='Changement de statut'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mise à jour'
        verbose_name_plural = 'Mises à jour'

    def __str__(self):
        return f"Update #{self.id} for {self.issue.title}"