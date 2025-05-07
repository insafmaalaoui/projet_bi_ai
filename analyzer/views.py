from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
import warnings
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
import numpy as np
from django.shortcuts import get_object_or_404, render, redirect
from .forms import LoginForm, RegisterForm, ProfileForm, PredictionForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import ContactForm
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
import json
from django.utils import timezone
from datetime import timedelta
from .models import Message, Activity
from .utils import log_activity

# Ignorer les avertissements spécifiques de version scikit-learn
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# Chemins relatifs à BASE_DIR (ou adapte si nécessaire selon ton projet)
model_path = os.path.join(settings.BASE_DIR, 'analyzer', 'models', 'mon_modele2.pkl')
encoder_campaign_path = os.path.join(settings.BASE_DIR, 'analyzer', 'models', 'label_encoder_Campaign_Type.pkl')
encoder_channel_path = os.path.join(settings.BASE_DIR, 'analyzer', 'models', 'label_encoder_Channel_Used.pkl')

# Chargement unique au démarrage
model = joblib.load(model_path)
encoder_campaign = joblib.load(encoder_campaign_path)
encoder_channel = joblib.load(encoder_channel_path)

# Vérifie si l'utilisateur est admin (superuser)
def is_admin(user):
    return user.is_superuser

# Vue pour la page d'accueil
# views.py




def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save()
            
            # Envoi d'email de confirmation
            send_mail(
                subject='Confirmation de votre message - ChannelOptimizer',
                message=f'Bonjour {message.name},\n\nNous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais.\n\nCordialement,\nL\'équipe ChannelOptimizer',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.email],
                fail_silently=True,
            )
            
            # Notification à l'administrateur
            send_mail(
                subject='Nouveau message de contact',
                message=f'Nouveau message de {message.name} ({message.email}):\n\n{message.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST],
                fail_silently=True,
            )
            
            messages.success(request, "Votre message a été envoyé avec succès!")
            return redirect('index')
    else:
        form = ContactForm()
    
    return render(request, 'index.html', {'form': form})

# Vue pour la page de connexion
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                if user.is_superuser:
                    return redirect('admin_dashboard')  # Rediriger vers admin_dashboard si c'est un superuser
                else:
                    return redirect('index') 
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# Vue pour la page d'inscription
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# Vue pour la page de prédiction
@login_required
def predict(request):
    prediction = None
    error_message = None

    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            try:
                # Encodage des variables catégorielles
                if data['Campaign_Type'] not in encoder_campaign.classes_:
                    error_message = f"Type de campagne inconnu : {data['Campaign_Type']}. Valeurs possibles : {', '.join(encoder_campaign.classes_)}"
                elif data['Channel_Used'] not in encoder_channel.classes_:
                    error_message = f"Canal inconnu : {data['Channel_Used']}. Valeurs possibles : {', '.join(encoder_channel.classes_)}"
                else:
                    encoded_campaign = encoder_campaign.transform([data['Campaign_Type']])[0]
                    encoded_channel = encoder_channel.transform([data['Channel_Used']])[0]

                    # Données numériques
                    numeric_data = [
                        data['Conversion_Rate'],
                        data['Acquisition_Cost'],
                        data['Engagement_Score'],
                        data['CTR'],
                        data['CPC']
                    ]

                    # Fusion des données
                    final_input = np.array([[encoded_campaign, encoded_channel, *numeric_data]])

                    # Prédiction
                    prediction = model.predict(final_input)[0]
                    prediction = round(prediction, 2)
                    log_activity(
                           user=request.user,
                           title="prédiction",
                           description=f"A fait une prédiction",
                           activity_type='success'
        ) 

            except Exception as e:
                error_message = f"Erreur lors de la prédiction : {str(e)}"

    else:
        form = PredictionForm()

    return render(request, 'predict.html', {
        'form': form,
        'prediction': prediction,
        'error': error_message
    })
  

# Vue pour la page de tableau de bord
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# Vue pour la page de déconnexion
def logout_view(request):
    logout(request)
    return redirect('login')

# Vue pour la page de profil

# Vue pour la page de profil
@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            
            # Enregistrer l'activité
            log_activity(
                user=request.user,
                title="Mise à jour du profil",
                description=f"A mis à jour son profil",
                activity_type='success'
            )
            
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Récupérer les activités récentes de l'utilisateur
    recent_activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    return render(request, 'profile.html', {
        'form': form,
        'recent_activities': recent_activities
    })
# Vue pour la page de déconnexion
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès!")
    return redirect('login')

# Vue pour changer le mot de passe
@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Vérifier que le mot de passe actuel est correct
        if not request.user.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
            return redirect('profile')
        
        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            return redirect('profile')
        
        # Changer le mot de passe
        request.user.set_password(new_password)
        request.user.save()
        
        # Enregistrer l'activité
        log_activity(
            user=request.user,
            title="Changement de mot de passe",
            description=f"A changé son mot de passe",
            activity_type='warning'
        )
        
        # Reconnecter l'utilisateur avec le nouveau mot de passe
        user = authenticate(username=request.user.username, password=new_password)
        auth_login(request, user)
        
        messages.success(request, "Votre mot de passe a été changé avec succès!")
        return redirect('profile')
    
    return redirect('profile')



def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.")
            return redirect('index')
    else:
        form = ContactForm()
    
    return render(request, 'index.html', {'form': form})





@login_required
@staff_member_required
def admin_dashboard(request):
    """Vue pour afficher le tableau de bord administrateur"""
    # Statistiques générales
    users_count = User.objects.count()
    messages_count = Message.objects.count()
    
    # Calculer le taux de réponse
    total_messages = Message.objects.count()
    responded_messages = Message.objects.filter(status='responded').count()
    response_rate = round((responded_messages / total_messages) * 100) if total_messages > 0 else 0
    
    # Calculer le temps de réponse moyen (en heures)
    avg_response_time = 0
    responded_messages_with_time = Message.objects.filter(status='responded', responded_at__isnull=False)
    if responded_messages_with_time.exists():
        total_response_time = sum([(m.responded_at - m.created_at).total_seconds() for m in responded_messages_with_time])
        avg_response_time = round(total_response_time / (3600 * responded_messages_with_time.count()), 1)
    
    # Croissance mensuelle (simulée pour l'exemple)
    users_growth = 15
    messages_growth = 23
    response_rate_growth = 8
    avg_response_time_improvement = 12
    
    # Données pour les graphiques
    # Messages par jour (7 derniers jours)
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    
    new_messages_data = []
    responded_messages_data = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        new_count = Message.objects.filter(created_at__date=date, status='new').count()
        responded_count = Message.objects.filter(created_at__date=date, status='responded').count()
        new_messages_data.append(new_count)
        responded_messages_data.append(responded_count)
    
    messages_chart_data = {
        'labels': json.dumps(dates),
        'new_messages': json.dumps(new_messages_data),
        'responded_messages': json.dumps(responded_messages_data)
    }
    
    # Utilisateurs actifs par jour (7 derniers jours)
    active_users_data = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        # Simuler des données d'utilisateurs actifs
        # Dans un cas réel, vous pourriez utiliser des données de connexion ou d'activité
        active_count = User.objects.filter(last_login__date=date).count()
        active_users_data.append(active_count)
    
    users_chart_data = {
        'labels': json.dumps(dates),
        'active_users': json.dumps(active_users_data)
    }
    
    # Activités récentes
    recent_activities = Activity.objects.all().order_by('-timestamp')[:5]
    
    # Messages récents
    recent_messages = Message.objects.all().order_by('-created_at')[:5]
    
    # Compteur de nouveaux messages
    new_messages_count = Message.objects.filter(status='new').count()
    
    context = {
        'stats': {
            'users_count': users_count,
            'messages_count': messages_count,
            'response_rate': response_rate,
            'avg_response_time': avg_response_time,
            'users_growth': users_growth,
            'messages_growth': messages_growth,
            'response_rate_growth': response_rate_growth,
            'avg_response_time_improvement': avg_response_time_improvement
        },
        'messages_chart_data': messages_chart_data,
        'users_chart_data': users_chart_data,
        'recent_activities': recent_activities,
        'recent_messages': recent_messages,
        'new_messages_count': new_messages_count
    }
    
    return render(request, 'admin/admin_dashboard.html', context)
@login_required
@staff_member_required
def admin_messages(request):
    """Vue pour gérer les messages"""
    # Filtres
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Requête de base
    messages_query = Message.objects.all()
    
    # Appliquer les filtres
    if status_filter:
        messages_query = messages_query.filter(status=status_filter)
    
    if date_from:
        messages_query = messages_query.filter(created_at__date__gte=date_from)
    
    if date_to:
        messages_query = messages_query.filter(created_at__date__lte=date_to)
    
    if search:
        messages_query = messages_query.filter(
            Q(name__icontains=search) | 
            Q(email__icontains=search) | 
            Q(subject__icontains=search) | 
            Q(message__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(messages_query, 10)  # 10 messages par page
    page = request.GET.get('page', 1)
    messages_list = paginator.get_page(page)
    
    # Compteur de nouveaux messages
    new_messages_count = Message.objects.filter(status='new').count()
    
    context = {
        'messages_list': messages_list,
        'new_messages_count': new_messages_count
    }
    
    return render(request, 'admin/admin_messages.html', context)
@login_required
@staff_member_required
def admin_message_respond(request, message_id):
    """Vue pour répondre à un message"""
    message_obj = get_object_or_404(Message, id=message_id)
    
    if request.method == 'POST':
        response = request.POST.get('response', '')
        
        if response:
            message_obj.response = response
            message_obj.status = 'responded'
            message_obj.responded_at = timezone.now()
            message_obj.responded_by = request.user
            message_obj.save()
            
            # Enregistrer l'activité
            log_activity(
                user=request.user,
                title="Réponse à un message",
                description=f"A répondu au message de {message_obj.name}",
                activity_type='success'
            )
            
            messages.success(request, "Votre réponse a été envoyée avec succès.")
        else:
            messages.error(request, "La réponse ne peut pas être vide.")
    
    return redirect('admin_messages')
@login_required
@staff_member_required
def admin_message_delete(request, message_id):
    """Vue pour supprimer un message"""
    message_obj = get_object_or_404(Message, id=message_id)
    
    if request.method == 'POST':
        message_name = message_obj.name
        message_obj.delete()
        
        # Enregistrer l'activité
        log_activity(
            user=request.user,
            title="Suppression d'un message",
            description=f"A supprimé le message de {message_name}",
            activity_type='danger'
        )
        
        messages.success(request, "Le message a été supprimé avec succès.")
    
    return redirect('admin_messages')
@login_required
@staff_member_required
def admin_message_delete_multiple(request):
    """Vue pour supprimer plusieurs messages"""
    if request.method == 'POST':
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])
        
        if message_ids:
            deleted_count = Message.objects.filter(id__in=message_ids).delete()[0]
            
            # Enregistrer l'activité
            log_activity(
                user=request.user,
                title="Suppression multiple de messages",
                description=f"A supprimé {deleted_count} messages",
                activity_type='danger'
            )
            
            return JsonResponse({'success': True, 'count': deleted_count})
    
    return JsonResponse({'success': False})
@login_required
@staff_member_required
def admin_users(request):
    """Vue pour gérer les utilisateurs"""
    # Filtres
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    search = request.GET.get('search', '')
    
    # Requête de base
    users_query = User.objects.all()
    
    # Appliquer les filtres
    if role_filter:
        if role_filter == 'admin':
            users_query = users_query.filter(is_superuser=True)
        elif role_filter == 'staff':
            users_query = users_query.filter(is_staff=True, is_superuser=False)
        elif role_filter == 'user':
            users_query = users_query.filter(is_staff=False, is_superuser=False)
    
    if status_filter:
        is_active = status_filter == 'active'
        users_query = users_query.filter(is_active=is_active)
    
    if date_from:
        users_query = users_query.filter(date_joined__date__gte=date_from)
    
    if search:
        users_query = users_query.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) | 
            Q(first_name__icontains=search) | 
            Q(last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users_query, 10)  # 10 utilisateurs par page
    page = request.GET.get('page', 1)
    users_list = paginator.get_page(page)
    
    # Compteur de nouveaux messages
    new_messages_count = Message.objects.filter(status='new').count()
    
    context = {
        'users_list': users_list,
        'new_messages_count': new_messages_count
    }
    
    return render(request, 'admin/admin_users.html', context)
@login_required
@staff_member_required
def admin_user_add(request):
    """Vue pour ajouter un utilisateur"""
    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'user')
        
        if username and email and password:
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur est déjà utilisé.")
                return redirect('admin_users')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "Cette adresse email est déjà utilisée.")
                return redirect('admin_users')
            
            # Créer l'utilisateur
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Définir le rôle
            if role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            elif role == 'staff':
                user.is_staff = True
            
            user.save()
            
            # Enregistrer l'activité
            log_activity(
                user=request.user,
                title="Création d'un utilisateur",
                description=f"A créé l'utilisateur {username}",
                activity_type='success'
            )
            
            messages.success(request, "L'utilisateur a été créé avec succès.")
        else:
            messages.error(request, "Tous les champs sont obligatoires.")
    
    return redirect('admin_users')
@login_required
@staff_member_required
def admin_user_edit(request, user_id):
    """Vue pour modifier un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == 'on'
        
        if username and email:
            # Vérifier si le nom d'utilisateur est déjà utilisé par un autre utilisateur
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, "Ce nom d'utilisateur est déjà utilisé.")
                return redirect('admin_users')
            
            # Vérifier si l'email est déjà utilisé par un autre utilisateur
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, "Cette adresse email est déjà utilisée.")
                return redirect('admin_users')
            
            # Mettre à jour les informations de base
            user_obj.username = username
            user_obj.email = email
            user_obj.is_active = is_active
            
            # Mettre à jour le mot de passe si fourni
            if password:
                user_obj.set_password(password)
            
            # Mettre à jour le rôle
            if role == 'admin':
                user_obj.is_staff = True
                user_obj.is_superuser = True
            elif role == 'staff':
                user_obj.is_staff = True
                user_obj.is_superuser = False
            else:
                user_obj.is_staff = False
                user_obj.is_superuser = False
            
            user_obj.save()
            
            # Enregistrer l'activité
            log_activity(
                user=request.user,
                title="Modification d'un utilisateur",
                description=f"A modifié l'utilisateur {username}",
                activity_type='warning'
            )
            
            messages.success(request, "L'utilisateur a été modifié avec succès.")
        else:
            messages.error(request, "Le nom d'utilisateur et l'email sont obligatoires.")
    
    return redirect('admin_users')
@login_required
@staff_member_required
def admin_user_delete(request, user_id):
    """Vue pour supprimer un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Empêcher la suppression de son propre compte
        if user_obj == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('admin_users')
        
        username = user_obj.username
        user_obj.delete()
        
        # Enregistrer l'activité
        log_activity(
            user=request.user,
            title="Suppression d'un utilisateur",
            description=f"A supprimé l'utilisateur {username}",
            activity_type='danger'
        )
        
        messages.success(request, "L'utilisateur a été supprimé avec succès.")
    
    return redirect('admin_users')
@login_required
@staff_member_required
def admin_api_message(request, message_id):
    """API pour récupérer les détails d'un message"""
    message_obj = get_object_or_404(Message, id=message_id)
    
    data = {
        'id': message_obj.id,
        'name': message_obj.name,
        'email': message_obj.email,
        'subject': message_obj.subject or '(Sans sujet)',
        'message': message_obj.message,
        'status': message_obj.status,
        'created_at': message_obj.created_at.strftime('%d/%m/%Y %H:%M'),
        'response': message_obj.response,
        'responded_at': message_obj.responded_at.strftime('%d/%m/%Y %H:%M') if message_obj.responded_at else None,
        'responded_by': message_obj.responded_by.username if message_obj.responded_by else None
    }
    
    return JsonResponse(data)
@login_required
@staff_member_required
def admin_api_user(request, user_id):
    """API pour récupérer les détails d'un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    data = {
        'id': user_obj.id,
        'username': user_obj.username,
        'email': user_obj.email,
        'is_active': user_obj.is_active,
        'is_staff': user_obj.is_staff,
        'is_superuser': user_obj.is_superuser,
        'date_joined': user_obj.date_joined.strftime('%d/%m/%Y %H:%M'),
        'last_login': user_obj.last_login.strftime('%d/%m/%Y %H:%M') if user_obj.last_login else None
    }
    
    return JsonResponse(data)
@login_required
@staff_member_required
def admin_settings(request):
    """Vue pour les paramètres d'administration"""
    # Compteur de nouveaux messages
    new_messages_count = Message.objects.filter(status='new').count()
    
    context = {
        'new_messages_count': new_messages_count
    }
    
    return render(request, 'admin/admin_settings.html', context)
@login_required
def user_messages(request):
    """Vue pour afficher les messages de l'utilisateur et les réponses des administrateurs"""
    # Récupérer les messages de l'utilisateur connecté en filtrant par son email
    user_messages = Message.objects.filter(email=request.user.email).order_by('-created_at')
    
    context = {
        'user_messages': user_messages,
    }
    
    return render(request, 'user_messages.html', context)
