"""
URL configuration for marketing_analyzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore

# Dans votre fichier urls.py principal (probablement dans le dossier du projet)


# Personnaliser le titre et l'en-tête de l'admin
admin.site.site_header = "Administration Analyzer"
admin.site.site_title = "Analyzer Admin"
admin.site.index_title = "Bienvenue dans l'interface d'administration d'Analyzer"


urlpatterns = [
    path('admin/', admin.site.urls),  # Panneau d'administration Django
    path('', include('analyzer.urls')), 
    path('logout/', views.logout_view, name='logout'), # Inclure les URLs de l'application analyzer
]