from .models import SupportMessage, Report, UserProfile

def notification_data(request):
    """Get counts and recent items for the notification bell"""
    if not request.user.is_authenticated:
        return {}
    
    context = {}
    notifications = []
    
    # Safely get the user's role (prevents crashes for admin/superusers)
    role = None
    try:
        role = request.user.profile.role
    except UserProfile.DoesNotExist:
        pass
        
    # 1. USER NOTIFICATIONS (Replies to their messages)
    if role in ['student', 'staff']:
        unread_msgs = SupportMessage.objects.filter(
            user=request.user,
            admin_response__isnull=False,
            is_read_by_user=False
        ).order_by('-created_at')[:5]
        
        for msg in unread_msgs:
            notifications.append({
                'type': 'message',
                'title': 'New Counselor Reply',
                'text': f"Re: {msg.subject}",
                'url': f"/support/?selected={msg.id}", # type: ignore
                'icon': 'fa-envelope',
                'color': 'text-primary'
            })
            
    # 2. COUNSELOR NOTIFICATIONS (New messages & Assigned cases)
    elif role == 'counselor':
        unread_msgs = SupportMessage.objects.filter(is_read=False).order_by('-created_at')[:3]
        for msg in unread_msgs:
            notifications.append({
                'type': 'message',
                'title': 'New Message',
                'text': f"From: {msg.user.get_full_name() or msg.user.username}",
                'url': f"/counselor/messages/?selected={msg.id}", # type: ignore
                'icon': 'fa-envelope',
                'color': 'text-info'
            })
            
        # Safe call for incident type display
        assigned_reports = Report.objects.filter(assigned_to=request.user, status='pending')[:3]
        for rep in assigned_reports:
            notifications.append({
                'type': 'report',
                'title': 'Assigned Case',
                'text': f"Report #{rep.id} - {rep.incident_type}", # type: ignore
                'url': f"/counselor/report/{rep.id}/", # type: ignore
                'icon': 'fa-file-alt',
                'color': 'text-warning'
            })
            
    # 3. ADMIN/SECURITY NOTIFICATIONS (New reports)
    elif request.user.is_staff or request.user.is_superuser or role == 'security':
        new_reports = Report.objects.filter(status='pending').order_by('-created_at')[:5]
        for rep in new_reports:
            notifications.append({
                'type': 'report',
                'title': 'New Incident Report',
                'text': f"#{rep.id} - {rep.location}", # type: ignore
                'url': f"/admin-report/{rep.id}/", # type: ignore
                'icon': 'fa-exclamation-triangle',
                'color': 'text-danger'
            })

    context['notifications'] = notifications
    context['notification_count'] = len(notifications)
    
    return context