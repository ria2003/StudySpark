from .models import Notification

def notifications_processor(request):
    """Add unread notification count to all templates"""
    if request.user.is_authenticated:
        # Always query the database for the most accurate count
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        
        # Store in session for future requests
        request.session['unread_notifications_count'] = unread_count
        
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}