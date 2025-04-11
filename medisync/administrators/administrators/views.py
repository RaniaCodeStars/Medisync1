from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Doctor, Patient, Appointment, Notification, Speciality, AdminActivityLog
from .forms import DoctorApprovalForm, PatientForm, AppointmentForm, SpecialityForm, NotificationForm
from django.contrib import messages

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    # Statistiques principales
    stats = {
        'total_doctors': Doctor.objects.filter(status='approved').count(),
        'total_patients': Patient.objects.count(),
        'total_appointments': Appointment.objects.filter(
            date_time__date=timezone.now().date()
        ).count(),
        'pending_issues': Notification.objects.filter(is_read=False).count(),
        'pending_doctors': Doctor.objects.filter(status='pending')
                            .select_related('user', 'speciality')[:3],
        'recent_activities': AdminActivityLog.objects.select_related('admin')
                              .order_by('-created_at')[:5],
        'recent_appointments': Appointment.objects.select_related(
            'patient__user', 'doctor__user'
        ).order_by('-date_time')[:5],
    }
    
    # Calcul des pourcentages
    def get_percentage(queryset, days):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        current = queryset.filter(created_at__range=(start_date, end_date)).count()
        previous = queryset.filter(
            created_at__range=(start_date - timedelta(days=days), start_date)
        ).count()
        return round((current - previous) / previous * 100, 1) if previous else 0
    
    stats.update({
        'doctors_percentage': get_percentage(Doctor.objects.filter(status='approved'), 30),
        'patients_percentage': get_percentage(Patient.objects.all(), 30),
        'appointments_percentage': get_percentage(Appointment.objects.all(), 30),
        'issues_percentage': -3,  # Exemple statique
    })
    
    # Données pour les graphiques
    def get_appointments_data(days=30):
        date_from = timezone.now() - timedelta(days=days)
        appointments = Appointment.objects.filter(
            date_time__gte=date_from
        ).extra({
            'date': "date(date_time)"
        }).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return {
            'labels': [app['date'].strftime('%Y-%m-%d') for app in appointments],
            'data': [app['count'] for app in appointments],
        }
    
    def get_specialties_data():
        specialties = Speciality.objects.annotate(
            doctor_count=Count('doctor', filter=Q(doctor__status='approved'))
        ).order_by('-doctor_count')[:5]
        
        return {
            'labels': [spec.name for spec in specialties],
            'data': [spec.doctor_count for spec in specialties],
        }
    
    context = {
        **stats,
        'appointments_stats': get_appointments_data(),
        'specialties_stats': get_specialties_data(),
    }
    
    return render(request, 'accounts/dashboard_admin.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorApprovalForm(request.POST, instance=doctor)
        if form.is_valid():
            doctor = form.save()
            
            # Créer une notification pour le médecin
            Notification.objects.create(
                user=doctor.user,
                title="Votre compte a été approuvé",
                message="Félicitations! Votre compte médecin a été approuvé.",
                notification_type='doctor_approval'
            )
            
            # Enregistrer l'activité
            AdminActivityLog.objects.create(
                admin=request.user,
                action='doctor_approval',
                details=f"A approuvé le médecin {doctor.user.get_full_name()}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, "Médecin approuvé avec succès")
            return redirect('administrators:admin_dashboard')
    else:
        form = DoctorApprovalForm(instance=doctor)
    
    return render(request, 'administrators/approve_doctor.html', {'form': form, 'doctor': doctor})

@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        doctor.status = 'rejected'
        doctor.save()
        
        # Créer une notification pour le médecin
        Notification.objects.create(
            user=doctor.user,
            title="Votre compte a été rejeté",
            message="Votre demande de compte médecin a été rejetée.",
            notification_type='doctor_approval'
        )
        
        # Enregistrer l'activité
        AdminActivityLog.objects.create(
            admin=request.user,
            action='doctor_approval',
            details=f"A rejeté le médecin {doctor.user.get_full_name()}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, "Médecin rejeté avec succès")
        return redirect('administrators:admin_dashboard')
    
    return render(request, 'administrators/reject_doctor.html', {'doctor': doctor})

@login_required
@user_passes_test(lambda u: u.is_staff)
def doctor_list(request):
    doctors = Doctor.objects.select_related('user', 'speciality').all()
    return render(request, 'administrators/doctor_list.html', {'doctors': doctors})

@login_required
@user_passes_test(lambda u: u.is_staff)
def patient_list(request):
    patients = Patient.objects.select_related('user').all()
    return render(request, 'administrators/patient_list.html', {'patients': patients})

@login_required
@user_passes_test(lambda u: u.is_staff)
def appointment_list(request):
    appointments = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).all()
    return render(request, 'administrators/appointment_list.html', {'appointments': appointments})

# API Views
@login_required
@user_passes_test(lambda u: u.is_staff)
def api_appointments_stats(request):
    days = int(request.GET.get('days', 30))
    date_from = timezone.now() - timedelta(days=days)
    
    appointments = Appointment.objects.filter(
        date_time__gte=date_from
    ).extra({
        'date': "date(date_time)"
    }).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    return JsonResponse({
        'labels': [app['date'].strftime('%Y-%m-%d') for app in appointments],
        'data': [app['count'] for app in appointments],
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def api_specialties_stats(request):
    stats_type = request.GET.get('type', 'doctors')
    
    if stats_type == 'appointments':
        specialties = Speciality.objects.annotate(
            count=Count('doctor__appointment')
        ).order_by('-count')[:5]
    elif stats_type == 'revenue':
        # Exemple: 50€ par rendez-vous
        specialties = Speciality.objects.annotate(
            count=Count('doctor__appointment') * 50
        ).order_by('-count')[:5]
    else:
        # Par défaut: médecins par spécialité
        specialties = Speciality.objects.annotate(
            count=Count('doctor', filter=Q(doctor__status='approved'))
        ).order_by('-count')[:5]
    
    return JsonResponse({
        'labels': [spec.name for spec in specialties],
        'data': [spec.count for spec in specialties],
    })