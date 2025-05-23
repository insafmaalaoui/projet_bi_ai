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
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import datetime
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import pandas as pd
from django.shortcuts import render
import os
import plotly.express as px
import plotly.offline as opy
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as opy
import os

def dashboard_view(request):
    # Récupération des données
    # Option 1: Depuis un fichier CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'data_to_use.csv')
    df = pd.read_csv(csv_path)
    
    # Option 2: Depuis la base de données (décommentez si vous préférez utiliser les données de la BD)
    # queryset = MarketingData.objects.all()
    # df = pd.DataFrame.from_records(queryset.values())
    
    # Préparation des KPIs
    kpis = {
        'total_campaigns': len(df),
        'avg_roi': round(df['ROI'].mean(), 2),
        'max_roi': round(df['ROI'].max(), 2),
        'avg_conversion': round(df['Conversion_Rate'].mean(), 2),
        'total_cost': round(df['Acquisition_Cost'].sum(), 2),
        'avg_cpc': round(df['CPC'].mean(), 2),
    }
    
    # Préparation des données pour les graphiques
    # 1. Distribution du ROI
    roi_hist = px.histogram(
        df, 
        x='ROI',
        nbins=20,
        title='Distribution du ROI',
        color_discrete_sequence=['#7AAEB5'],
        opacity=0.8
    )
    roi_hist.update_layout(
        xaxis_title='ROI',
        yaxis_title='Nombre de campagnes',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    # 2. ROI par type de campagne
    campaign_roi = df.groupby('Campaign_Type')['ROI'].mean().reset_index()
    campaign_roi_fig = px.bar(
        campaign_roi,
        x='Campaign_Type',
        y='ROI',
        title='ROI moyen par type de campagne',
        color='ROI',
        color_continuous_scale='Teal',
        text_auto='.2f'
    )
    campaign_roi_fig.update_layout(
        xaxis_title='Type de campagne',
        yaxis_title='ROI moyen',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    # 3. ROI par canal
    channel_roi = df.groupby('Channel_Used')['ROI'].mean().reset_index()
    channel_roi_fig = px.bar(
        channel_roi,
        x='Channel_Used',
        y='ROI',
        title='ROI moyen par canal',
        color='ROI',
        color_continuous_scale='Teal',
        text_auto='.2f'
    )
    channel_roi_fig.update_layout(
        xaxis_title='Canal',
        yaxis_title='ROI moyen',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    # 4. Relation entre coût d'acquisition et ROI
    scatter_fig = px.scatter(
        df,
        x='Acquisition_Cost',
        y='ROI',
        color='Channel_Used',
        size='Engagement_Score',
        hover_data=['Conversion_Rate', 'CTR', 'CPC'],
        title='Relation entre coût d\'acquisition et ROI'
    )
    scatter_fig.update_layout(
        xaxis_title='Coût d\'acquisition',
        yaxis_title='ROI',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=450
    )
    
    # 5. Heatmap des corrélations
    corr = df[['ROI', 'Conversion_Rate', 'Acquisition_Cost', 'Engagement_Score', 'CTR', 'CPC']].corr()
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='Teal',
        zmin=-1, zmax=1
    ))
    heatmap_fig.update_layout(
        title='Matrice de corrélation',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    # 6. Taux de conversion par canal
    conversion_by_channel = df.groupby('Campaign_Type')['Conversion_Rate'].mean().reset_index()
    conversion_fig = px.bar(
        conversion_by_channel,
        x='Campaign_Type',
        y='Conversion_Rate',
        title='Taux de conversion moyen par compagne',
        color='Conversion_Rate',
        color_continuous_scale='Teal',
        text_auto='.2f'
    )
    conversion_fig.update_layout(
        xaxis_title='Canal',
        yaxis_title='Taux de conversion (%)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    # 7. Radar chart pour comparer les canaux
    # Préparation des données pour le radar chart
    radar_df = df.groupby('Channel_Used')[['ROI', 'Conversion_Rate', 'Engagement_Score', 'CTR']].mean()
    radar_df = radar_df.reset_index()
    
    # Normalisation des données pour le radar chart
    for col in ['ROI', 'Conversion_Rate', 'Engagement_Score', 'CTR']:
        max_val = radar_df[col].max()
        radar_df[f'{col}_norm'] = radar_df[col] / max_val * 10
    
    # Création du radar chart
    radar_fig = go.Figure()
    
    for channel in radar_df['Channel_Used'].unique():
        channel_data = radar_df[radar_df['Channel_Used'] == channel]
        radar_fig.add_trace(go.Scatterpolar(
            r=[
                channel_data['ROI_norm'].values[0],
                channel_data['Conversion_Rate_norm'].values[0],
                channel_data['Engagement_Score_norm'].values[0],
                channel_data['CTR_norm'].values[0],
                channel_data['ROI_norm'].values[0]  # Répéter le premier pour fermer le polygone
            ],
            theta=['ROI', 'Taux de conversion', 'Engagement', 'CTR', 'ROI'],
            fill='toself',
            name=f'Canal {channel}'
        ))
    
    radar_fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        title='Comparaison des performances par canal',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=450
    )
    
    # 8. Tableau récapitulatif des données
    table_data = df.describe().round(2).reset_index()
    table_data.columns = ['Statistique'] + list(df.describe().columns)
    
    table_fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(table_data.columns),
            fill_color='#7AAEB5',
            align='left',
            font=dict(color='white', size=12)
        ),
        cells=dict(
            values=[table_data[col] for col in table_data.columns],
            fill_color='rgba(0,0,0,0)',
            align='left'
        )
    )])
    table_fig.update_layout(
        title='Statistiques descriptives',
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    # Conversion des figures en HTML
    plots = {
        'roi_hist': opy.plot(roi_hist, auto_open=False, output_type='div'),
        'campaign_roi': opy.plot(campaign_roi_fig, auto_open=False, output_type='div'),
        'channel_roi': opy.plot(channel_roi_fig, auto_open=False, output_type='div'),
        'scatter': opy.plot(scatter_fig, auto_open=False, output_type='div'),
        'heatmap': opy.plot(heatmap_fig, auto_open=False, output_type='div'),
        'conversion': opy.plot(conversion_fig, auto_open=False, output_type='div'),
        'radar': opy.plot(radar_fig, auto_open=False, output_type='div'),
        'table': opy.plot(table_fig, auto_open=False, output_type='div'),
    }
    
    # Préparation des données pour le tableau
    table_html = df.head(10).to_html(classes='table table-striped table-hover', index=False)
    
    # Contexte pour le template
    context = {
        'kpis': kpis,
        'plots': plots,
        'table_html': table_html,
        'summary': df.describe().to_html(classes='table table-striped table-sm'),
    }
    
    return render(request, 'dashboard.html', context)

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
                    # Dans votre fonction predict, après avoir calculé la prédiction
                    request.session['prediction'] = prediction
                    request.session['form_data'] = form.cleaned_data

            except Exception as e:
                error_message = f"Erreur lors de la prédiction : {str(e)}"

    else:
        form = PredictionForm()

    return render(request, 'predict.html', {
        'form': form,
        'prediction': prediction,
        'error': error_message
    })
  



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


def generate_pdf(request):
    # Récupérer les données de prédiction et du formulaire depuis la session
    prediction = request.session.get('prediction', None)
    form_data = request.session.get('form_data', {})
    
    # Si aucune prédiction n'est disponible, rediriger vers la page de prédiction
    if prediction is None:
        return redirect('predict')
    
    # Préparer le contexte pour le template PDF
    context = {
        'prediction': prediction,
        'form_data': form_data,
        'date': datetime.datetime.now().strftime("%d/%m/%Y"),
        'recommendations': generate_recommendations(prediction, form_data)
    }
    
    # Charger le template HTML pour le PDF
    template = get_template('pdf/prediction_report.html')
    html = template.render(context)
    
    # Créer un objet PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    # Vérifier si la création du PDF a réussi
    if not pdf.err:
        # Définir les en-têtes de la réponse pour le téléchargement
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rapport_prediction.pdf"'
        return response
    
    # En cas d'erreur, renvoyer une page d'erreur
    return HttpResponse("Une erreur est survenue lors de la génération du PDF", status=400)

def generate_recommendations(prediction, form_data):
    """Génère des recommandations personnalisées basées sur les résultats de prédiction et les données du formulaire"""
    recommendations = []
    
    # Recommandations de base
    recommendations.append("Assurez-vous d'avoir une stratégie de contenu cohérente sur tous vos canaux marketing.")
    recommendations.append("Suivez régulièrement vos KPIs pour ajuster votre stratégie en temps réel.")
    
    # Recommandations basées sur le ROI prédit
    if prediction:
        if prediction >= 4:
            recommendations.append("Votre ROI prévu est excellent. Envisagez d'augmenter votre budget marketing pour maximiser vos résultats.")
            recommendations.append("Documentez votre stratégie actuelle pour reproduire ce succès dans vos futures campagnes.")
        elif prediction >= 2.5:
            recommendations.append("Votre ROI prévu est bon. Cherchez à optimiser certains aspects de votre campagne pour améliorer davantage vos résultats.")
            recommendations.append("Testez différentes approches créatives pour identifier ce qui résonne le mieux avec votre audience.")
        else:
            recommendations.append("Votre ROI prévu est à améliorer. Réévaluez votre stratégie marketing et envisagez de réallouer votre budget.")
            recommendations.append("Concentrez-vous sur un ou deux canaux marketing au lieu de disperser vos efforts.")
    
    # Recommandations basées sur les données du formulaire
    if 'canal' in form_data:
        canal = form_data['canal'].lower()
        if 'Facebook' in canal:
            recommendations.append("Pour vos campagnes facebook, privilégiez des objets personnalisés et testez différentes heures d'envoi.")
            recommendations.append("Segmentez votre liste d'emails pour des messages plus ciblés et pertinents.")
        elif 'social' in canal or 'réseaux' in canal:
            recommendations.append("Sur les réseaux sociaux, publiez régulièrement et engagez-vous avec votre audience.")
            recommendations.append("Utilisez des visuels de haute qualité et adaptez votre contenu à chaque plateforme.")
        elif 'Influencer' in canal or 'référencement' in canal:
            recommendations.append("Pour améliorer votre Influencer, concentrez-vous sur des mots-clés pertinents et créez du contenu de qualité.")
            recommendations.append("Travaillez sur l'expérience utilisateur de votre site pour réduire le taux de rebond.")
        elif 'Display' in canal or 'publicité' in canal:
            recommendations.append("Pour vos campagnes Display, affinez régulièrement vos mots-clés et optimisez vos enchères.")
            recommendations.append("Créez des pages d'atterrissage spécifiques pour chaque campagne publicitaire.")
    
    # Limiter à 5 recommandations maximum
    return recommendations[:5]


# Load environment variables
load_dotenv()

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('user_input', '').strip()

            if not user_input:
                return JsonResponse({'error': 'Message vide.'}, status=400)

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return JsonResponse({'error': 'Clé API manquante.'}, status=500)

            # Initialize chat history with domain-specific context
            if 'chat_history' not in request.session:
                request.session['chat_history'] = [{
                    "role": "user",
                    "parts": [{
                        "text": (
                            "Tu es un assistant IA expert en marketing digital, "
                            "spécialisé dans l’analyse des campagnes publicitaires, "
                            "la segmentation de marché, l'optimisation des performances, "
                            "et le conseil stratégique pour les entreprises."
                        )
                    }]
                }]

            # Append new user input
            request.session['chat_history'].append({
                "role": "user",
                "parts": [{"text": user_input}]
            })

            # Send to Gemini API
            prompt = {"contents": request.session['chat_history']}
            headers = {"Content-Type": "application/json"}
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            response = requests.post(api_url, headers=headers, json=prompt)

            if response.status_code == 200:
                response_data = response.json()
                bot_reply = response_data['candidates'][0]['content']['parts'][0]['text']

                # Save bot response in history
                request.session['chat_history'].append({
                    "role": "model",
                    "parts": [{"text": bot_reply}]
                })
                request.session.modified = True

                return JsonResponse({'response': bot_reply})
            else:
                return JsonResponse({
                    'error': f"Erreur API Gemini : {response.status_code}, détails : {response.text}"
                }, status=500)

        except Exception as e:
            return JsonResponse({'error': f'Erreur serveur : {str(e)}'}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée. Utilisez POST.'}, status=400)

def chatbot_page(request):
    return render(request, 'chatbot.html')