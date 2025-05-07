from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
   
    path('dashboard/', views.dashboard, name='dashboard'),
    path('predict/', views.predict, name='predict'),
    path('profile/', views.profile, name='profile'),
 
    path('admin/admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Messages
    path('admin/messages/', views.admin_messages, name='admin_messages'),
    path('admin/messages/respond/<int:message_id>/', views.admin_message_respond, name='admin_message_respond'),
    path('admin/messages/delete/<int:message_id>/', views.admin_message_delete, name='admin_message_delete'),
    path('admin/messages/delete-multiple/', views.admin_message_delete_multiple, name='admin_message_delete_multiple'),
    
    # Utilisateurs
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/add/', views.admin_user_add, name='admin_user_add'),
    path('admin/users/edit/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/delete/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    
    # API
    path('admin/api/message/<int:message_id>/', views.admin_api_message, name='admin_api_message'),
    path('admin/api/user/<int:user_id>/', views.admin_api_user, name='admin_api_user'),
    
    # Paramètres
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('logout/', views.logout_view, name='logout'),
   
    path('change-password/', views.change_password, name='change_password'),
     path('messages/', views.user_messages, name='user_messages'),
  
]


  