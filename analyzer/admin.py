from django.contrib import admin
from .models import Message, Activity


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Informations', {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Réponse', {
            'fields': ('status', 'response', 'responded_at', 'responded_by')
        }),
    )

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'timestamp')
    list_filter = ('type', 'timestamp', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('timestamp',)
    
