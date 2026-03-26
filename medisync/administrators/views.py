from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from patients.models import Patient
from datetime import datetime, timedelta
from medecins.models import Doctor ,Specialty 
from core.models import Notification
from clinics.models import Clinic , RendezVous
from .models import    AdminActivityLog
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib import messages
from medecins.models import Doctor
from appointments.models import Appointment
from .models import NotificationGenerale
from administrators.models import ReportedIssue ,IssueCategory,IssueUpdate
from django.utils import timezone
from django.shortcuts import render
from medecins.models import Doctor  # Adapter selon ton nom d'app
from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_staff)



def dashboard_admin(request):
    # Statistiques d'activité des médecins
    doctor_stats = Doctor.get_active_stats(30)
    total_doctors = Doctor.objects.count()

    # Statistiques d'activité des patients
    patient_stats = Patient.get_active_stats(30)

    # Clinics en attente
    latest_pending_clinics = Clinic.objects.filter(status='pending').order_by('-id')[:3]

    # Médecins en attente de validation
    latest_pending_doctors = Doctor.objects.filter(status='pending').order_by('-created_at')[:3]

    # Période de filtrage
    period = request.GET.get('period', 'today').lower()
    today = timezone.now().date()

    if period == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == 'this week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == 'this month':
        start_date = today.replace(day=1)
        end_date = start_date.replace(month=start_date.month+1) if start_date.month != 12 else start_date.replace(year=start_date.year+1, month=1)
    else:
        start_date, end_date, period = today, today + timedelta(days=1), 'today'

    # Statistiques rendez-vous
    appointment_stats = {
        'total': Appointment.objects.filter(date__month=timezone.now().month).count(),
        'confirmed': Appointment.objects.filter(status='confirmed', date__month=timezone.now().month).count(),
        'pending': Appointment.objects.filter(status='pending', date__month=timezone.now().month).count(),
        'cancelled': Appointment.objects.filter(status='cancelled', date__month=timezone.now().month).count(),
    }

    # Rendez-vous récents
    recent_appointments = Appointment.objects.filter(
        date__range=(start_date, end_date)
    ).select_related('patient', 'doctor__user', 'doctor__specialty').order_by('date', 'time')[:10]

    # Formatage des rendez-vous
    formatted_appointments = [{
        'id': f"#AP-{app.id}",
        'patient_name': f"{app.patient.patient_profile.nom}",
        'doctor_name': f"Dr. {app.doctor.nom}",
        'datetime': f"{app.date.strftime('%d/%m/%Y')} {app.time.strftime('%H:%M')}",
        'specialty': app.doctor.specialty if hasattr(app.doctor, 'specialty') and app.doctor.specialty else "Généraliste",
        'status': app.status,
        'status_display': app.get_status_display(),
        'status_class': {
            'confirmed': 'success',
            'pending': 'warning',
            'cancelled': 'danger',
        }.get(app.status, 'secondary')
    } for app in recent_appointments]

    # Statistiques cliniques
    clinic_total = Clinic.objects.count()
    clinic_pending = Clinic.objects.filter(status='pending').count()
    clinic_approved = Clinic.objects.filter(status='approved').count()

    try:
        approved_pct = round((clinic_approved/clinic_total)*100, 1)
        pending_pct = round((clinic_pending/clinic_total)*100, 1)
    except ZeroDivisionError:
        approved_pct = pending_pct = 0.0

    clinic_stats = {
        'total': clinic_total,
        'pending': clinic_pending,
        'approved': clinic_approved,
        'approved_pct': approved_pct,
        'pending_pct': pending_pct,
    }

    # Contexte
    context = {
        'doctor_stats': doctor_stats,
        'clinic_stats': clinic_stats,
        'latest_pending_clinics': latest_pending_clinics,
        'total_doctors': total_doctors,
        'patient_stats': patient_stats,
        'latest_pending_doctors': latest_pending_doctors,
        'recent_appointments': Appointment.objects.select_related('patient', 'doctor__user').order_by('-date')[:5],
        'total_appointments': Appointment.objects.filter(date=today).count(),
        'appointment_stats': appointment_stats,
    }

    return render(request, 'administrators/dashboard_admin.html', context)

'''
    # Calcul des statistiques
    doctor_stats = Doctor.get_active_stats(30)
    doctor_trend = Doctor.get_activity_trend(30)
    patient_stats = Patient.get_active_stats(30)
    patient_trend = Patient.get_activity_trend(30)
    appointment_stats = {
        'total': Appointment.objects.filter(
            date__month=timezone.now().month
        ).count(),
        'confirmed': Appointment.objects.filter(
            status='confirmed',
            date__month=timezone.now().month
        ).count(),
        'pending': Appointment.objects.filter(
            status='pending',
            date__month=timezone.now().month
        ).count(),
        'cancelled': Appointment.objects.filter(
            status='cancelled',
            date__month=timezone.now().month
        ).count(),
        'trend': calculate_appointment_trend(),  # Fonction custom (voir plus bas)
        'is_increasing': True  # À remplacer par votre logique
    }
    
    # Déterminer la période demandée
    period = request.GET.get('period', 'today').lower()
    today = timezone.now().date()
    
    if period == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == 'this week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == 'this month':
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year+1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month+1)
    else:
        start_date = today
        end_date = today + timedelta(days=1)
        period = 'today'
    # Récupérer les rendez-vous (attention à l'indentation)
    recent_appointments = Appointment.objects.filter(
        date__range=(start_date, end_date)
    ).select_related('patient__user', 'doctor__user', 'doctor__specialty').order_by('date', 'time')[:10]
    
    # Formater les données
    formatted_appointments = []
    for app in recent_appointments:
        formatted_appointments.append({
            'id': f"#AP-{app.id}",
            'patient_name': f"{app.patient.user.last_name} {app.patient.user.first_name}",
            'doctor_name': f"Dr. {app.doctor.user.last_name}",
            'datetime': f"{app.date.strftime('%d/%m/%Y')} {app.time.strftime('%H:%M')}",
            'specialty': app.doctor.specialty if hasattr(app.doctor, 'specialty') and app.doctor.specialty else "Généraliste",
            'status': app.status,
            'status_display': app.get_status_display(),
            'status_class': {
                'confirmed': 'success',
                'pending': 'warning',
                'cancelled': 'danger',
            }.get(app.status, 'secondary')
        })
    doctor_id = request.POST.get('doctor_id')
    action = request.POST.get('action')
        
    try:
            with transaction.atomic():
                doctor = Doctor.objects.select_related('user__profile').get(id=doctor_id)
                
                if action == 'approve':
                    doctor.status = 'approved'
                    doctor.save()
                    
                    doctor.user.profile.is_verified = True
                    doctor.user.profile.save()
                    
                    messages.success(request, f"Le médecin {doctor.nom} {doctor.prenom} a été approuvé avec succès.")
                
                elif action == 'reject':
                    doctor_name = f"{doctor.nom} {doctor.prenom}"
                    doctor.delete()
                    messages.success(request, f"Le médecin {doctor_name} a été rejeté.")
                    
    except Doctor.DoesNotExist:
            messages.error(request, "Le médecin spécifié n'existe pas.")

    # Statistiques d'activité (6 derniers mois)
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)  # 6 mois
    
    # Patients par mois
    patients_data = (
        Patient.objects.filter(user__date_joined__range=(start_date, end_date))
        .annotate(month=TruncMonth('user__date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Rendez-vous par mois
    appointments_data = (
    Appointment.objects.filter(date__range=(start_date, end_date))
    .annotate(month=TruncMonth('date'))
    .values('month')
    .annotate(count=Count('id'))
    .order_by('month')
)
    
    # Préparation des données pour le graphique
    months = []
    patients_counts = []
    appointments_counts = []
    
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        month_str = current_month.strftime('%b')  # Format court (Jan, Feb...)
        months.append(month_str)
        
        # Patients
        patient_count = next(
            (item['count'] for item in patients_data 
             if item['month'].month == current_month.month 
             and item['month'].year == current_month.year),
            0
        )
        patients_counts.append(patient_count)
        
        # Rendez-vous
        appointment_count = next(
            (item['count'] for item in appointments_data 
             if item['month'].month == current_month.month 
             and item['month'].year == current_month.year),
            0
        )
        appointments_counts.append(appointment_count)
        
        current_month = (current_month.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    activity_stats = {
        'months': months[-6:],  # Garder seulement les 6 derniers mois
        'patients': patients_counts[-6:],
        'appointments': appointments_counts[-6:],
    }    
     # Récupérer les notifications pour l'administrateur
    notifications = NotificationGenerale.objects.filter(recipient=request.user).order_by('-created_at')

    
    # Préparation du contexte
    context = {
        'pending_doctors': Doctor.objects.filter(status='pending')
                                      .select_related('user', 'specialty')[:3],
        # Statistiques principales
        'total_doctors': Doctor.objects.filter(status='approved').count(),
        'total_patients': Patient.objects.count(),
        'total_appointments': Appointment.objects.filter(date=timezone.now().date()).count(),
        'pending_issues': Notification.objects.filter(is_read=False).count(),
        
        'recent_appointments': formatted_appointments,
        'current_period': period,
        'periods': {
            'today': "Aujourd'hui",
            'this week': "Cette Semaine",
            'this month': "Ce Mois",
        },
        # Listes
        
        'recent_activities': AdminActivityLog.objects.select_related('admin')
                                                  .order_by('-timestamp')[:5],
        'recent_appointments': Appointment.objects.select_related('patient__user', 'doctor__user')
                                               .order_by('-date')[:5],
        
        # Statistiques d'activité
        'doctor_stats': doctor_stats,
        'activity_trend': doctor_trend,
        'patient_stats': patient_stats,
        'patient_trend': patient_trend,
        'appointment_stats': appointment_stats,
        'activity_stats': activity_stats,
        # Notifications
        'notifications': notifications,
        # Autres données du dashboard
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.filter(status='approved').count(),
        'today_appointments': Appointment.objects.filter(
            date=timezone.now().date()
        ).count(),
        
    }
'''

def calculate_appointment_trend():
    """Calcule la tendance mensuelle des rendez-vous"""
    current_month = timezone.now().month
    last_month = (timezone.now() - timezone.timedelta(days=30)).month
    
    current_count = Appointment.objects.filter(
        date__month=current_month
    ).count()
    
    last_count = Appointment.objects.filter(
        date__month=last_month
    ).count()
    
    try:
        return round((current_count - last_count) / last_count * 100, 1)
    except ZeroDivisionError:
        return 0.0

#gestion des speciality

from medecins.models import Specialty
from .forms import SpecialityForm
from django.contrib import messages

# Liste + Ajout
def gerer_specialites(request):
    specialites = Specialty.objects.all()

    if request.method == 'POST':
        form = SpecialityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Spécialité ajoutée avec succès.")
            return redirect('administrators:gerer_specialites')
    else:
        form = SpecialityForm()

    return render(request, 'administrators/gerer_specialites.html', {
        'form': form,
        'specialites': specialites
    })



def supprimer_specialite(request, pk):
    specialite = get_object_or_404(Specialty, pk=pk)
    specialite.delete()
    messages.success(request, "Spécialité supprimée avec succès.")
    return redirect('administrators:gerer_specialites')








#gestion patientS:

from django.views.generic import ListView
from patients.models import Patient
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator

def is_admin(user):
    return user.is_authenticated and user.profile.role == 'ADMIN'  # adapte selon ton modèle


from django.core.paginator import Paginator

from django.db.models import Q
from django.core.paginator import Paginator
from accounts.models import Profile  # Si Profile est dans accounts


def PatientListView(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page')

    # On filtre uniquement les patients dont l'utilisateur a le rôle 'PATIENT'
    patients = Patient.objects.filter(user__profile__role='PATIENT')

    if query:
        patients = patients.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(user__email__icontains=query)
        )

    paginator = Paginator(patients, 25)
    page_obj = paginator.get_page(page_number)

    return render(request, 'administrators/patients_list.html', {
        'page_obj': page_obj,
        'search_query': query
    })

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from patients.models import Patient
from .forms import PatientForm  # On supposera qu'on a un formulaire pour créer/mettre à jour un patient

from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import PatientForm
from accounts.models import Profile
from django.db import IntegrityError
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.contrib.auth import get_user_model





@staff_member_required
def PatientCreateView(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient créé avec succès.")
            return redirect('administrators:admin_patients_list')
    else:
        form = PatientForm()

    return render(request, 'administrators/patient_form.html', {
        'form': form,
        'editing': False,
    })




from .forms import DoctorForm
@staff_member_required
def DoctorCreateView(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre inscription a été soumise avec succès. En attente de validation.")
            return redirect('administrators:doctor_list')
    else:
        form = DoctorForm()

    return render(request, 'administrators/doctor_add.html', {
        'form': form
    })

'''
from accounts.forms import PatientSignupForm



@staff_member_required
def PatientCreateView(request):
   if request.method == 'POST':
        form = PatientSignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # C'est un User, pas un Patient
            print(f"Utilisateur créé: {user.email}")  # Debug
            # Vérification que le profil existe
            if hasattr(user, 'profile'):
                    print(f"Profil trouvé, rôle: {user.profile.role}")  # Debug
            else:
                    print("Aucun profil trouvé!")  # Debug
                    Profile.objects.create(user=user, role='PATIENT')  # Création de secours
                    
        else:
         form = PatientSignupForm()

        return render(request, 'administrators/patient_form.html', {
        'form': form
    })
    '''
from django.views.generic import DetailView

class PatientDetailView(DetailView):
    model = Patient
    template_name = 'administrators/patient_detail.html'
    context_object_name = 'patient'


from django.views.generic.edit import UpdateView

from django.urls import reverse_lazy
from django.views.generic import UpdateView

from accounts.models import NotificationAdmin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required


from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
  # adapte le chemin si nécessaire

@staff_member_required
def PatientUpdateView(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient, editing=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient mis à jour avec succès.")
            return redirect('administrators:admin_patients_list')
    else:
        form = PatientForm(instance=patient, editing=True)

    return render(request, 'administrators/patient_update.html', {
        'form': form,
        'editing': True,
        'patient': patient,
    })




from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView

from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin

class PatientDeleteView(SuccessMessageMixin, DeleteView):
    model = Patient
    template_name = 'administrators/patient_confirm_delete.html'
    success_url = reverse_lazy('administrators:admin_patients_list')
    success_message = "Le patient a été supprimé avec succès."

    def delete(self, request, *args, **kwargs):
        patient = self.get_object()
        user = patient.user
        
        # Notification avant suppression
        NotificationAdmin.objects.create(
            User=user,
            sujet='Compte supprimé',
            message='Votre compte patient a été supprimé par un administrateur.'
        )
        
        # Suppression
        user.delete()  # Supprime aussi le patient via CASCADE
        return super().delete(request, *args, **kwargs)
from django.shortcuts import render
from django.views.generic import TemplateView
from patients.models import Patient

class PatientStatsView(TemplateView):
    template_name = 'administrators/patient_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques d'activité
        activity_stats = Patient.get_active_stats(days=30)

        # Tendance d'activité
        activity_trend = Patient.get_activity_trend(days=30)

        # Répartition par sexe (Homme/Femme)
        gender_distribution = Patient.get_gender_distribution()

        # Répartition par groupe sanguin
        blood_group_distribution = Patient.get_blood_group_distribution()

        # Tendances de création des patients
        creation_trend = Patient.get_creation_trend(days=30)

        # Ajouter les statistiques au contexte
        context.update({
            'activity_stats': activity_stats,
            'activity_trend': activity_trend,
            'gender_distribution': gender_distribution,
            'blood_group_distribution': blood_group_distribution,
            'creation_trend': creation_trend,
        })

        return context
    
import csv
from django.http import HttpResponse
from django.views.generic import View
from patients.models import Patient

class PatientExportView(View):
    def get(self, request, *args, **kwargs):
        # Créer la réponse HTTP avec le bon type de contenu pour un fichier CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="patients.csv"'

        # Créer un writer CSV
        writer = csv.writer(response)
        
        # Écrire l'en-tête du fichier CSV
        writer.writerow(['Nom', 'Prénom', 'Email', 'Sexe', 'Groupe sanguin', 'Allergies', 'Compte RIP'])

        # Ajouter les données des patients au fichier CSV
        patients = Patient.objects.all()
        for patient in patients:
            writer.writerow([
                patient.nom,
                patient.prenom,
                patient.user.email,
                patient.get_sex_display(),
                patient.blood_group,
                patient.allergies,
                patient.compte_RIP,
            ])

        return response









import csv
from django.shortcuts import render
from django.http import HttpResponse
from patients.models import Patient
from django.contrib import messages
from django.views.generic import View
from django.core.exceptions import ValidationError

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
import csv

class PatientImportView(View):
    def get(self, request, *args, **kwargs):
        # Afficher la page d'import avec le formulaire
        return render(request, 'administrators/import_patients.html')

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            messages.error(request, "Aucun fichier sélectionné.")
            return redirect('administrators:admin_patient_import')

        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être un fichier CSV.")
            return redirect('administrators:admin_patient_import')

        try:
            file_data = csv_file.read().decode('utf-8')
            lines = file_data.splitlines()
            reader = csv.reader(lines)

            next(reader)  # Passer la première ligne (headers)

            for row in reader:
                if len(row) < 7:
                    continue

                user_data = {
                    'username': row[2],
                    'email': row[2],
                }

                user, created = User.objects.get_or_create(email=user_data['email'], defaults=user_data)

                if created:
                    user.set_password('defaultpassword123')  # Si tu veux, tu peux fixer un mot de passe par défaut
                    user.save()

                patient_data = {
                    'nom': row[0],
                    'prenom': row[1],
                    'user': user,
                    'sex': 'M' if row[3] == 'Homme' else 'F',
                    'blood_group': row[4],
                    'allergies': row[5],
                    'compte_RIP': row[6],
                }

                Patient.objects.update_or_create(user=user, defaults=patient_data)

            messages.success(request, "L'importation des patients a réussi.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation : {str(e)}")

        return redirect('administrators:admin_patient_import')







#gestion medecins
from django.shortcuts import render
from django.views.generic import ListView
from medecins.models import Doctor, Specialty
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

class DoctorListView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'administrators/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 10
    

    
    def get_queryset(self):
     queryset = super().get_queryset().select_related('specialty', 'user')

    # ✅ Appliquer le filtre d'archivage
     queryset = queryset.filter(is_archived=False)
     

    # ➡️ Montre uniquement les médecins validés
     queryset = queryset.filter(status='approved')

    # Tous tes autres filtres restent :
     specialty = self.request.GET.get('specialty')
     if specialty:
         queryset = queryset.filter(specialty__id=specialty)

     status = self.request.GET.get('status')
     if status:
        queryset = queryset.filter(status=status)

     online = self.request.GET.get('online')
     if online:
         queryset = queryset.filter(accept_online_appointments=True)

     location = self.request.GET.get('location')
     if location:
         queryset = queryset.filter(location=location)

     search = self.request.GET.get('search')
     if search:
         queryset = queryset.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(specialty__nom__icontains=search)
        )

     return queryset.order_by('nom', 'prenom')

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specialties'] = Specialty.objects.all()
        context['wilaya_choices'] = WILAYA_CHOICES
        context['active_stats'] = Doctor.get_active_stats()
        context['activity_trend'] = Doctor.get_activity_trend()
        
        # Garder les filtres actuels
        context['current_specialty'] = self.request.GET.get('specialty', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_location'] = self.request.GET.get('location', '')
        context['current_online'] = self.request.GET.get('online', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        return context
    





from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy

class DoctorDetailView(LoginRequiredMixin, DetailView):
    model = Doctor
    template_name = 'administrators/doctor_detail.html'
    context_object_name = 'doctor'

    def get_queryset(self):
        show_archived = self.request.GET.get('archived') == '1'
        if show_archived:
            return Doctor.objects.filter(is_archived=True)
        return Doctor.objects.filter(is_archived=False)


from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from medecins.models import Doctor

class ArchiveDoctorView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        doctor.is_archived = True
        doctor.save()
        messages.success(request, f"Le médecin {doctor.nom} {doctor.prenom} a été archivé.")
        return redirect('administrators:doctor_list')









from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from medecins.models import Doctor
from .forms import DoctorForm  # Ton form personnalisé si tu en as un !

class DoctorUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        form = DoctorForm(instance=doctor)
        return render(request, 'administrators/doctor_form.html', {
            'form': form,
            'editing': True,
            'doctor': doctor,
        })

    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect(reverse('administrators:doctor_list'))  # Redirige vers la liste des médecins admin
        return render(request, 'administrators/doctor_form.html', {
            'form': form,
            'editing': True,
            'doctor': doctor,
        })
    

# views.py
from django.views.generic import ListView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect

class PendingDoctorsView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'administrators/doctor_validation.html'
    context_object_name = 'pending_doctors'
    paginate_by = 10
    
    def get_queryset(self):
        return Doctor.objects.filter(status='pending').select_related(
            'specialty', 'user__profile'
        ).order_by('-validation_requested_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Validation des médecins'
        return context


from django.conf import settings
class ApproveDoctorView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor.objects.select_related('user__profile', 'specialty'), pk=pk)
        
        if doctor.status != 'pending':
            messages.error(request, "Ce médecin n'est pas en attente de validation.")
            return redirect('administrators:doctor_validation')
        
        # Mettre à jour le statut du médecin
        doctor.status = 'approved'
        doctor.save()
        
        # Mettre à jour le profil utilisateur
        doctor.user.profile.is_verified = True
        doctor.user.profile.save()
        
        # Envoyer l'email de confirmation
        subject = 'Votre compte Medisync a été approuvé'
        html_message = render_to_string('administrators/doctor_approved.html', {
            'doctor': doctor,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[doctor.user.email],
                html_message=html_message,
                fail_silently=False
            )
            email_sent = True
        except Exception as e:
            email_sent = False
            print(f"Erreur envoi email: {e}")
        
        # Créer une notification
        NotificationGenerale.objects.create(
            sender=request.user,
            recipient=doctor.user,
            type='validation_compte',
            title='Compte approuvé',
            message="Votre compte médecin a été approuvé par l'administrateur.",
        )
        
        
        messages.success(request, f"Le médecin {doctor.nom} {doctor.prenom} a été approuvé avec succès.")
        
        return render(request, 'administrators/approve_doctor.html', {
            'doctor': doctor,
            'email_sent': email_sent,
            'site_url': settings.SITE_URL
        })

class RejectDoctorView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor.objects.select_related('user'), pk=pk)
        
        if doctor.status != 'pending':
            messages.error(request, "Ce médecin n'est pas en attente de validation.")
            return redirect('administrators:doctor_validation')
        
        doctor_name = f"{doctor.nom} {doctor.prenom}"
        doctor_email = doctor.user.email
        
        # Création de la notification avant suppression
        NotificationGenerale.objects.create(
            sender=request.user,
            recipient=doctor.user,
            type='rejet_compte',
            title='Compte rejeté',
            message="Votre demande d'inscription en tant que médecin a été rejetée.",
        )
        
        
        doctor.delete()
        
        # Envoi d'email
        subject = 'Votre demande de compte Medisync a été rejetée'
        html_message = render_to_string('administrators/doctor_rejected.html', {
            'doctor_name': doctor_name,
            'admin': request.user
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            None,
            [doctor_email],
            html_message=html_message,
            fail_silently=False
        )
        
        messages.success(request, f"La demande du médecin {doctor_name} a été rejetée.")
        return redirect('administrators:doctor_validation')


from django.db import models  # Ajoutez cette ligne en haut du fichier
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count  # Ajoutez cette ligne à la place

class DoctorStatsView(View):
    template_name = 'administrators/doctor_stats.html'
    
    def get(self, request):
        # Statistiques de base
        total_doctors = Doctor.objects.count()
        approved_doctors = Doctor.objects.filter(status='approved').count()
        pending_doctors = Doctor.objects.filter(status='pending').count()
        
        # Statistiques d'activité
        active_stats = Doctor.get_active_stats()
        activity_trend = Doctor.get_activity_trend()
        
        # Répartition par spécialité
       
# Puis modifiez les lignes concernées :
        specialties_stats = Doctor.objects.filter(status='approved')\
                                .values('specialty__nom')\
                                .annotate(count=Count('id'))\
                                .order_by('-count')

        location_stats = Doctor.objects.filter(status='approved')\
                             .values('location')\
                             .annotate(count=Count('id'))\
                             .order_by('-count')
        
        # Nouveaux médecins (30 derniers jours)
        new_doctors = Doctor.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30))
        
        context = {
            'page_title': 'Statistiques des Médecins',
            'total_doctors': total_doctors,
            'approved_doctors': approved_doctors,
            'pending_doctors': pending_doctors,
            'active_stats': active_stats,
            'activity_trend': activity_trend,
            'specialties_stats': specialties_stats,
            'location_stats': location_stats,
            'new_doctors_count': new_doctors.count(),
        }
        return render(request, self.template_name, context)










 
#gestion clinic

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from clinics.models import Clinic, ClinicDoctor ,WILAYA_CHOICES
from .forms import ClinicForm, ClinicDoctorFormSet
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from clinics.models import Clinic, ClinicDoctor
from .forms import ClinicForm, ClinicDoctorFormSet
from django.shortcuts import redirect

class ClinicListView(LoginRequiredMixin, ListView):
    model = Clinic
    template_name = 'administrators/clinic_list.html'
    context_object_name = 'clinics'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(user__is_active=True)
        
        # Filtrage par localisation
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location=location)
            
        # Filtrage par nom
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset.select_related('user').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wilaya_choices'] = WILAYA_CHOICES
        context['current_location'] = self.request.GET.get('location', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context

class ClinicDetailView(LoginRequiredMixin, DetailView):
    model = Clinic
    template_name = 'administrators/clinic_detail.html'
    context_object_name = 'clinic'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = self.object.doctors.all()
        return context
from django.views.generic import FormView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import ClinicSignupForm
from django.core.exceptions import ValidationError


class ClinicCreateView(FormView):
    template_name = 'administrators/clinic_form.html'
    form_class = ClinicSignupForm

    success_url = reverse_lazy('administrators:clinic-list')

    def form_valid(self, form):
        # Le formulaire save() crée user, profile, clinic
        user = form.save()
        messages.success(self.request, "La clinique a été créée avec succès. Un email de validation a été envoyé.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)


from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import ClinicSignupForm

class ClinicSignupView(FormView):
    template_name = 'administrators/clinic_signup.html'
    form_class = ClinicSignupForm
    success_url = reverse_lazy('administrators:clinic-list')

    def form_valid(self, form):
        user = form.save()  # Crée user + profile + clinic
        
        messages.success(self.request, "Votre clinique a été créée avec succès. Un email de validation vous sera envoyé.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la création de la clinique.")
        return super().form_invalid(form)


from django.views.generic import UpdateView

class ClinicUpdateView(UpdateView):
    model = Clinic
    template_name = 'administrators/clinic_form.html'
    fields = ['name', 'phone', 'adresse', 'location', 'site_web', 'description',
              'allow_reviews', 'appointment_policy', 'horaires', 'photos']  # Liste des champs modifiables
    success_url = reverse_lazy('administrators:clinic-list')

    def form_valid(self, form):
        messages.success(self.request, "La clinique a été mise à jour avec succès.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)

class ClinicDeleteView(LoginRequiredMixin, DeleteView):
    model = Clinic
    template_name = 'administrators/clinic_confirm_delete.html'
    success_url = reverse_lazy('administrators:clinic-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Clinique supprimée avec succès!")
        return super().delete(request, *args, **kwargs)
    
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def reject_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    if clinic.profile.is_verified:  # ou une autre condition selon ta logique
        messages.error(request, "Cette clinique a déjà été approuvée.")
        return redirect('administrators:pending_clinics')

    # Supprimer la clinique ou marquer comme rejetée
    user_email = clinic.user.email
    clinic_name = clinic.name
    clinic.delete()  # ou .status = "rejected", selon ta logique

    # Envoi d'un email de refus
    subject = "Votre inscription à Medisync a été refusée"
    html_message = render_to_string('administrators/clinic_rejected.html', {
        'clinic_name': clinic_name,
        'site_url': settings.SITE_URL,
    })
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False
        )
        messages.success(request, f"La clinique {clinic_name} a été rejetée et notifiée par email.")
    except Exception as e:
        print(f"Erreur envoi email de rejet : {e}")
        messages.warning(request, "La clinique a été rejetée, mais l'email n'a pas été envoyé.")

    return redirect('administrators:pending_clinics')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from clinics.models import Clinic
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.views.decorators.http import require_POST
@login_required
@user_passes_test(is_admin)


def pending_clinics(request):
    clinics = Clinic.objects.filter(user__is_active=False).select_related('user').prefetch_related('user__profile')

    if request.method == 'POST':
        clinic_id = request.POST.get('clinic_id')
        action = request.POST.get('action')
        
        try:
            clinic = Clinic.objects.get(id=clinic_id)
            if action == 'approve':
                clinic.user.is_active = True
                clinic.user.save()
                clinic.user.profile.is_verified = True
                clinic.user.profile.save()
                messages.success(request, f'La clinique {clinic.name} a été approuvée avec succès.')

                # ✅ Envoi email d'approbation
                subject = 'Votre compte clinique a été approuvé'
                html_message = render_to_string('administrators/clinic_approved.html', {
                    'clinic': clinic
                })
                plain_message = strip_tags(html_message)
                try:
                    send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [clinic.user.email],
                              html_message=html_message, fail_silently=False)
                except Exception as e:
                    print(f"[ERREUR EMAIL APPROBATION] {e}")

                # ✅ Notification interne
                NotificationGenerale.objects.create(
                    recipient=clinic.user,
                    type='compte_valide',
                    title='Votre compte a été approuvé',
                    message=f"Félicitations ! Votre compte clinique {clinic.name} a été approuvé."
                )

            elif action == 'reject':
                reason = request.POST.get('reason', '')
                messages.warning(request, f'La clinique {clinic.name} a été rejetée.')

                # ✅ Envoi email de rejet
                subject = 'Votre demande de création de compte a été rejetée'
                html_message = render_to_string('administrators/clinic_rejected.html', {
                    'clinic': clinic,
                    'reason': reason
                })
                plain_message = strip_tags(html_message)
                try:
                    send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [clinic.user.email],
                              html_message=html_message, fail_silently=False)
                except Exception as e:
                    print(f"[ERREUR EMAIL REJET] {e}")

                # ✅ Notification interne
                NotificationGenerale.objects.create(
                    recipient=clinic.user,
                    type='compte_rejete',
                    title='Votre compte a été rejeté',
                    message=f"Votre demande d'inscription pour {clinic.name} a été rejetée. Raison: {reason}"
                )

                clinic.delete()

            return redirect('administrators:pending_clinics')

        except Clinic.DoesNotExist:
            messages.error(request, 'Clinique introuvable')
            return redirect('administrators:pending_clinics')

    context = {
        'clinics': clinics,
        'page_title': 'Demandes d\'inscription des cliniques',
        'wilayas': WILAYA_CHOICES
    }
    return render(request, 'administrators/pending_clinic.html', context)

@require_POST
@login_required
@user_passes_test(is_admin)
def approve_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    clinic.user.is_active = True
    clinic.user.save()
    messages.success(request, f'La clinique {clinic.name} a été approuvée avec succès.')
    return redirect('pending_clinics')

@require_POST
@login_required
@user_passes_test(is_admin)
def reject_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    clinic_name = clinic.name
    clinic.delete()
    messages.success(request, f'La clinique {clinic_name} a été rejetée.')
    return redirect('pending_clinics')





#rendez-vous
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from appointments.models import Appointment



class AdminAppointmentsView(View):
    template_name = 'administrators/appointment_list.html'
    
    def get(self, request):
        # Filtres possibles
        status_filter = request.GET.get('status', 'all')
        date_filter = request.GET.get('date', None)
        doctor_filter = request.GET.get('doctor', None)
        emergency_filter = request.GET.get('emergency', None)
        
        # Base queryset
        appointments = Appointment.objects.select_related(
            'doctor__user', 'patient', 'consultation_reason'
        ).order_by('-date', '-time')
        
        # Application des filtres
        if status_filter != 'all':
            appointments = appointments.filter(status=status_filter)
            
        if date_filter:
            appointments = appointments.filter(date=date_filter)
            
        if doctor_filter:
            appointments = appointments.filter(doctor__id=doctor_filter)
            
        if emergency_filter == 'yes':
            appointments = appointments.filter(is_emergency=True)
        elif emergency_filter == 'no':
            appointments = appointments.filter(is_emergency=False)
        
        # Statistiques
        stats = Appointment.get_appointment_stats()
        
        # Prochains RDV (7 jours)
        upcoming = Appointment.objects.filter(
            date__gte=timezone.now().date(),
            date__lte=timezone.now().date() + timedelta(days=7)
        ).count()
        
        # RDV aujourd'hui
        today = Appointment.objects.filter(date=timezone.now().date()).count()
        
        context = {
            'page_title': 'Gestion des Rendez-vous',
            'appointments': appointments,
            'status_filter': status_filter,
            'date_filter': date_filter,
            'doctor_filter': doctor_filter,
            'emergency_filter': emergency_filter,
            'stats': stats,
            'upcoming': upcoming,
            'today': today,
        }
        return render(request, self.template_name, context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import NotificationGenerale

@login_required
def notification_list_view(request):
    # Vérifier que l'utilisateur est admin
    if not request.user.is_superuser:
        return redirect('home')  # Redirigez vers la page appropriée

    # Récupérer toutes les notifications non lues d'abord
    notifications = NotificationGenerale.objects.filter(recipient=request.user)\
                                .order_by('-is_read', '-created_at')
    
    # Pagination - 10 notifications par page
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'unread_count': NotificationGenerale.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    }
    
    return render(request, 'administrators/notification_list.html', context)

@login_required
def notification_detail_view(request, notification_id):
    notification = get_object_or_404(NotificationGenerale, 
                                   id=notification_id,
                                   recipient=request.user)
    
    # Marquer comme lu seulement si c'est une notification non lue
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    context = {
        'notification': notification,
        'sender_profile': getattr(notification.sender, 'doctor', None) or 
                         getattr(notification.sender, 'clinic', None)
    }
    
    return render(request, 'administrators/notification_detail.html', context)

@login_required
def mark_all_as_read_view(request):
    if request.method == 'POST' and request.user.is_superuser:
        NotificationGenerale.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

# administrators/views.py (ou votre fichier de contexte)
from .models import NotificationGenerale

def base_context(request):
    if request.user.is_authenticated:
        unread_count = NotificationGenerale.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    else:
        unread_count = 0
    
    return {
        'unread_notifications_count': unread_count
    }



from django.views import View
from django.shortcuts import render
from django.db.models import Count, Avg
from clinics.models import Clinic, ClinicDoctor


class ClinicStatsView(View):
    template_name = 'administrators/clinic_stats.html'

    def get(self, request):
        # Statistiques générales
        total_clinics = Clinic.objects.count()
        pending_clinics = Clinic.objects.filter(status='pending').count()
        approved_clinics = Clinic.objects.filter(status='approved').count()
        rejected_clinics = Clinic.objects.filter(status='rejected').count()

        # Répartition par wilaya
        clinics_by_location = (
            Clinic.objects.values('location')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Nombre moyen de médecins par clinique
        avg_doctors_per_clinic = Clinic.objects.annotate(num_doctors=Count('doctors')).aggregate(Avg('num_doctors'))['num_doctors__avg'] or 0

        # Répartition des médecins par spécialité (facultatif)
        doctors_by_specialty = (
    ClinicDoctor.objects.values('speciality__nom')
    .annotate(count=Count('id'))
    .order_by('-count')
)


        context = {
            'total_clinics': total_clinics,
            'pending_clinics': pending_clinics,
            'approved_clinics': approved_clinics,
            'rejected_clinics': rejected_clinics,
            'clinics_by_location': clinics_by_location,
            'avg_doctors_per_clinic': round(avg_doctors_per_clinic, 2),
            'doctors_by_specialty': doctors_by_specialty,
        }

        return render(request, self.template_name, context)
