from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Message
from .forms import MessageForm
from core.models import Notification

User = get_user_model()
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, CharField, F
from django.db.models.functions import Concat
from .models import Message
from .forms import MessageForm
from core.models import Notification


@login_required
def chat_view(request, username=None):
    receiver = None
    search_query = request.GET.get('search')
    search_results = []
    if search_query:
        search_results = User.objects.annotate(
            doctor_full_name=Concat('doctor_profile__nom', Value(' '), 'doctor_profile__prenom', output_field=CharField()),
            patient_full_name=Concat('patient_profile__nom', Value(' '), 'patient_profile__prenom', output_field=CharField()),
            full_name=Case(
                When(doctor_profile__isnull=False, then=F('doctor_full_name')),
                When(patient_profile__isnull=False, then=F('patient_full_name')),
                default=F('username'),
                output_field=CharField()
            )
        ).filter(full_name__icontains=search_query).exclude(id=request.user.id)


    # Récupération des utilisateurs avec leurs noms formatés
    sent_ids = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_ids = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    contact_ids = set(sent_ids) | set(received_ids)

    # On enlève les doublons et soi-même
    contact_ids = set(contact_ids) - {request.user.id}

    # Maintenant on récupère seulement ces utilisateurs-là avec noms formatés
    from django.db.models import Count, Q, IntegerField

    users = User.objects.filter(id__in=contact_ids).annotate(
        display_name=Case(
            When(doctor_profile__isnull=False, 
                 then=Concat(Value('Dr. '), 'doctor_profile__nom', Value(' '), 'doctor_profile__prenom')),
            When(patient_profile__isnull=False, 
                 then=Concat('patient_profile__nom', Value(' '), 'patient_profile__prenom')),
            default=F('username'),
            output_field=CharField()
        ),
        unread_count=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False),
            output_field=IntegerField()
        )
    )


    unread_count = Notification.objects.filter(user=request.user, status='unread').count()
    receiver = None
    messages = []

    if username:
        receiver = get_object_or_404(User, username=username)
        messages = Message.objects.filter(
            sender__in=[request.user, receiver],
            receiver__in=[request.user, receiver]
        ).annotate(
            sender_display_name=Case(
                When(sender__doctor_profile__isnull=False, 
                     then=Concat(Value('Dr. '), 'sender__doctor_profile__nom', Value(' '), 'sender__doctor_profile__prenom')),
                When(sender__patient_profile__isnull=False, 
                     then=Concat('sender__patient_profile__nom', Value(' '), 'sender__patient_profile__prenom')),
                default=F('sender__username'),
                output_field=CharField()
            )
        ).order_by('timestamp')
        # Marquer comme lus les messages que le receiver a envoyés à l'utilisateur connecté
        Message.objects.filter(sender=receiver, receiver=request.user, is_read=False).update(is_read=True)


    if request.method == 'POST' and receiver:
        form = MessageForm(request.POST)
        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.sender = request.user
            new_message.receiver = receiver
            new_message.save()
            return redirect('messaging:chat', username=receiver.username)
    else:
        form = MessageForm()

    # Nom du destinataire formaté
    receiver_name = None
    if receiver:
        if hasattr(receiver, 'doctor_profile'):
            receiver_name = f"Dr. {receiver.doctor_profile.nom} {receiver.doctor_profile.prenom}"
        elif hasattr(receiver, 'patient_profile'):
            receiver_name = f"{receiver.patient_profile.nom} {receiver.patient_profile.prenom}"
        else:
            receiver_name = receiver.username

    return render(request, 'messaging/chat.html', {
        'users': users,
        'receiver': receiver,
        'receiver_name': receiver_name,
        'messages': messages,
        'form': form,
        'unread_notification_count': unread_count,
        'search_results': search_results,
        'search_query': search_query,
    })




from django.http import HttpResponseForbidden

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    # L'utilisateur ne peut supprimer que ses propres messages
    if message.sender != request.user:
        return HttpResponseForbidden("Vous n'avez pas la permission de supprimer ce message.")

    message.delete()
    return redirect('messaging:chat', username=message.receiver.username)
