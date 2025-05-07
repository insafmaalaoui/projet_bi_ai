from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Message(models.Model):
    STATUS_CHOICES = (
        ('new', 'Nouveau'),

        ('responded', 'Répondu'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=200, verbose_name="Sujet", blank=True, null=True)
    message = models.TextField(verbose_name="Message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Statut")
    response = models.TextField(blank=True, null=True, verbose_name="Réponse")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    responded_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de réponse")
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="responses", verbose_name="Répondu par")
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d/%m/%Y')}"

class Activity(models.Model):
    TYPE_CHOICES = (
        ('primary', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('danger', 'Erreur'),
        ('info', 'Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities", verbose_name="Utilisateur")
    title = models.CharField(max_length=100, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info', verbose_name="Type")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.title} - {self.user.username} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    

