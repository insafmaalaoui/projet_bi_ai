from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Message

from django import forms

class PredictionForm(forms.Form):
    CAMPAIGN_CHOICES = [
        ('Email', 'Email Marketing'),
        ('Influencer', 'Influencer'),
        ('Display', 'Publicité en ligne'),
        ('Social Media', 'Social Media'),
        ('Search', 'Search'),
        
    ]

    CHANNEL_CHOICES = [
        ('Facebook', 'Facebook'),
        ('Google Ads', 'Google'),
        ('Instagram', 'Instagram'),
        ('Website', 'Website'),
        ('YouTube', 'YouTube'),
        ('Email', 'Email'),
        
    ]

    Campaign_Type = forms.ChoiceField(
        choices=CAMPAIGN_CHOICES,
        label="Type de campagne"
    )

    Channel_Used = forms.ChoiceField(
        choices=CHANNEL_CHOICES,
        label="Canal utilisé"
    )

    Conversion_Rate = forms.FloatField(
        label="Taux de conversion"
    )
    Acquisition_Cost = forms.FloatField(
        label="Coût d'acquisition"
    )
    Engagement_Score = forms.FloatField(
        label="Score d'engagement"
    )
    CTR = forms.FloatField(
        label="Taux de clic (CTR)"
    )
    CPC = forms.FloatField(
        label="Coût par clic (CPC)"
    )


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}))

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})
        
        
    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ContactForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com', 'pattern': '[^ @]*@[^ @]*'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': '7', 'placeholder': 'Votre message'}),
        }