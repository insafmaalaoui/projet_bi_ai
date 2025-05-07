from .models import Activity

def log_activity(user, title, description, activity_type='info'):
    """
    Enregistre une activité dans le système
    """
    Activity.objects.create(
        user=user,
        title=title,
        description=description,
        type=activity_type
    )
    return True
