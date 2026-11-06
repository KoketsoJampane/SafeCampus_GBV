from .emails import (
    send_welcome_email,
    send_support_message_notification,
    send_counselor_response_notification,
    send_report_assigned_notification,
    send_status_update_notification,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import OperationalError
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Report, SessionRecording, SupportMessage, Resource, UserProfile, AdminLog, ChatMessage
import json
import os
from datetime import datetime, timedelta
import uuid
import requests
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse

# ============================================
# HELPER FUNCTIONS
# ============================================

def is_admin(user):
    """Check if user has admin privileges"""
    return user.is_staff or user.is_superuser

def home_view(request):
    """Homepage view - shows the landing page"""
    return render(request, 'home.html')


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if they are staff/counselor/security and NOT verified
            try:
                profile = user.profile
                if profile.role in ['counselor', 'security', 'staff'] and not profile.is_verified and not user.is_superuser:
                    messages.error(request, 'Your account is pending verification. Please wait for an Admin to approve your qualifications.')
                    return render(request, 'login.html')
            except UserProfile.DoesNotExist:
                pass
                
            login(request, user)
            display_name = user.get_full_name() or user.username
            messages.success(request, f'Welcome back, {display_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'login.html')

def logout_view(request):
    """Log the user out and redirect to home"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'service_id': 'service_72cezic',          
        'template_id': 'template_sj6idei',        
        'public_key': 'jTyHz3WGGKqrZnPBb',        
    }
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        terms = request.POST.get('terms')

        if not terms:
            messages.error(request, 'You must agree to the Terms of Service.')
            return render(request, 'register.html', context)
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'register.html', context)
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'register.html', context)
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken. Please choose another.')
            return render(request, 'register.html', context)
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use another email.')
            return render(request, 'register.html', context)
        
        try:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else full_name
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password)
            )
            
            UserProfile.objects.create(
                user=user,
                role=role
            )
            
            if role in ['counselor', 'security', 'staff']:
                user.is_staff = False
                user.save()
            
            send_welcome_email(user)
            
            if role in ['counselor', 'security', 'staff']:
                messages.info(request, 'Your account has been created. An Admin must verify your account before you can log in.')
                return redirect('login')
            else:
                login(request, user)
                messages.success(request, f'Welcome to SafeCampus, {full_name}! 🎉')
                return redirect('dashboard') 
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'register.html', context)
    
    return render(request, 'register.html', context)


# ============================================
# FRONTEND VIEWS (User Facing)
# ============================================

@login_required
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    role = profile.role
    
    if role == 'counselor':
        return redirect('counselor_dashboard')
    elif role == 'security':
        return redirect('security_dashboard')
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    try:
        user_reports = Report.objects.filter(user=request.user)
        total_reports = user_reports.count()
        resolved_reports = user_reports.filter(status='resolved').count()
        in_progress = user_reports.filter(status__in=['pending', 'investigating']).count()
        community_members = User.objects.count()
    except OperationalError:
        total_reports = 0
        resolved_reports = 0
        in_progress = 0
        community_members = 1
    
    context = {
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'in_progress': in_progress,
        'community_members': community_members,
        'profile': profile,
    }
    return render(request, 'dashboard.html', context)


@login_required
def new_report_view(request):
    if request.method == 'POST':
        incident_type = request.POST.get('incident_type')
        location = request.POST.get('location')
        incident_date = request.POST.get('incident_date')
        description = request.POST.get('description')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        evidence_file = request.FILES.get('evidence_file')
        
        if not all([incident_type, location, incident_date, description]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'new_report.html')
        
        try:
            report = Report(
                user=request.user,
                incident_type=incident_type,
                location=location,
                incident_date=incident_date,
                description=description,
                is_anonymous=is_anonymous,
                status='pending'
            )
            
            evidence_filename = None
            if evidence_file:
                if evidence_file.size > 10485760:
                    messages.warning(request, 'File is too large (max 10MB). Report saved without evidence.')
                else:
                    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.pdf', '.doc', '.docx']
                    file_ext = os.path.splitext(evidence_file.name)[1].lower()
                    if file_ext in allowed_extensions:
                        unique_id = str(uuid.uuid4())[:8]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        evidence_filename = f"evidence_{request.user.id}_{timestamp}_{unique_id}{file_ext}"
                        messages.success(request, '✅ Evidence will be uploaded with your report!')
                    else:
                        messages.warning(request, 'File type not supported. Report saved without evidence.')
            
            report.save()
            
            # =====  SEND SECURITY ALERT =====
            try:
                security_officers = User.objects.filter(profile__role='security', profile__is_verified=True)
                
                if security_officers.exists():
                    for officer in security_officers:
                        if officer.email:
                            incident_type_display = getattr(report, 'get_incident_type_display', lambda: report.incident_type)()
                            subject = f"🚨 URGENT: New {incident_type_display} reported"
                            message = f"""
A new incident has been reported on SafeCampus.

TYPE: {incident_type_display}
LOCATION: {report.location}
DATE OF INCIDENT: {report.incident_date}

DESCRIPTION:
{report.description}

Please log in to the Security Dashboard immediately to review this incident.
"""
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [officer.email], fail_silently=True)
                            print(f"🚨 SECURITY ALERT SENT TO: {officer.email}")
                else:
                    print("⚠️ No verified security officers found in the system.")
            except Exception as e:
                print(f"Error sending security alert: {e}")
            # ===== END OF SECURITY ALERT =====
            
            if evidence_file and evidence_filename:
                if evidence_file.size <= 10485760:
                    report.evidence_file.save(evidence_filename, evidence_file)
                    report.save()
                    messages.success(request, '✅ Evidence uploaded successfully!')
            
            messages.success(request, '✅ Your report has been submitted successfully! Support will reach out within 24 hours.')
            return redirect('reports')
            
        except Exception as e:
            messages.error(request, f'Error submitting report: {str(e)}')
            return render(request, 'new_report.html')
    
    return render(request, 'new_report.html')


@login_required
def reports_view(request):
    try:
        reports = Report.objects.filter(user=request.user).order_by('-created_at')
    except OperationalError:
        reports = []
    return render(request, 'reports.html', {'reports': reports})


@login_required
def report_detail_view(request, report_id):
    report = get_object_or_404(Report, id=report_id, user=request.user)
    return render(request, 'report_detail.html', {'report': report})


@login_required
def support_view(request):
    if request.method == 'POST' and not request.POST.get('message_id'):
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        target_role = request.POST.get('target_role') 
        
        if subject and message_text:
            thread = SupportMessage.objects.create(
                user=request.user,
                subject=f"[{target_role.upper()}] {subject}", 
                message=message_text
            )
            ChatMessage.objects.create( 
                support_thread=thread,
                sender=request.user,
                message=message_text
            )
            messages.success(request, '✅ Chat started! A responder will reply soon.')
            return redirect(f'/support/?selected={thread.id}') 

    if request.method == 'POST' and request.POST.get('message_id'):
        thread_id = request.POST.get('message_id')
        reply_text = request.POST.get('message')
        
        if reply_text:
            thread = get_object_or_404(SupportMessage, id=thread_id, user=request.user)
            ChatMessage.objects.create( 
                support_thread=thread,
                sender=request.user,
                message=reply_text
            )
            return redirect(f'/support/?selected={thread_id}')

    support_messages = SupportMessage.objects.filter(user=request.user).order_by('-created_at')
    selected_id = request.GET.get('selected')
    selected_thread = None
    
    if selected_id:
        try:
            selected_thread = SupportMessage.objects.get(id=selected_id, user=request.user)
            if selected_thread.admin_response and not selected_thread.is_read_by_user:
                selected_thread.is_read_by_user = True
                selected_thread.save()
        except SupportMessage.DoesNotExist:
            pass
    
    context = {
        'support_messages': support_messages,
        'selected_id': selected_id,
        'selected_thread': selected_thread,
    }
    return render(request, 'support.html', context)


@login_required
def resources_view(request):
    resources = Resource.objects.all()
    
    if not resources.exists():
        default_resources = [
            {'title': 'Understanding Gender-Based Violence', 'description': 'Learn about the different forms of gender-based violence...', 'category': 'Education', 'icon': 'fas fa-book', 'link': '#', 'content': '<h4>What is GBV?</h4>'},
            {'title': 'Personal Safety Planning Guide', 'description': 'A step-by-step guide to creating a personalized safety plan...', 'category': 'Safety', 'icon': 'fas fa-shield-alt', 'link': '#', 'content': '<h4>Safety Plan</h4>'},
            {'title': 'Know Your Legal Rights', 'description': 'Information about your legal rights...', 'category': 'Legal', 'icon': 'fas fa-gavel', 'link': '#', 'content': '<h4>Legal Rights</h4>'},
            {'title': 'Healing and Recovery Resources', 'description': 'Resources for emotional healing...', 'category': 'Support', 'icon': 'fas fa-heart', 'link': '#', 'content': '<h4>Healing</h4>'},
            {'title': 'How to Support a Survivor', 'description': 'Learn how to support someone...', 'category': 'Support', 'icon': 'fas fa-hand-holding-heart', 'link': '#', 'content': '<h4>Support</h4>'},
            {'title': 'Digital Safety & Privacy', 'description': 'Learn how to protect yourself online...', 'category': 'Safety', 'icon': 'fas fa-laptop-shield', 'link': '#', 'content': '<h4>Digital Safety</h4>'},
            {'title': 'Emergency Contacts & Helplines', 'description': '24/7 emergency contact numbers...', 'category': 'Emergency', 'icon': 'fas fa-phone-alt', 'link': '#', 'content': '<h4>Emergency</h4>'},
        ]
        for res in default_resources:
            Resource.objects.create(**res)
        resources = Resource.objects.all()
    
    categories = Resource.objects.values_list('category', flat=True).distinct()
    return render(request, 'resources.html', {'resources': resources, 'categories': categories})


@login_required
def resource_detail_view(request, resource_id):
    try:
        resource = Resource.objects.get(id=resource_id)
    except Resource.DoesNotExist:
        messages.error(request, 'Resource not found.')
        return redirect('resources')
    return render(request, 'resource_detail.html', {'resource': resource})


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        bio = request.POST.get('bio')
        profile_picture = request.FILES.get('profile_picture')
        qualification_doc = request.FILES.get('qualification_doc') 
        
        if first_name: request.user.first_name = first_name
        if last_name: request.user.last_name = last_name
        if email: request.user.email = email
        request.user.save()

        if qualification_doc:
            profile.qualification_doc = qualification_doc
            profile.is_verified = False
            messages.info(request, 'Qualification uploaded. Admin will review it shortly.')
        
        if phone_number: profile.phone_number = phone_number
        if bio: profile.bio = bio
        
        if profile_picture:
            if profile_picture.size > 5242880:
                messages.error(request, 'Profile picture is too large. Maximum size is 5MB.')
            else:
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                file_ext = os.path.splitext(profile_picture.name)[1].lower()
                if file_ext in allowed_extensions:
                    profile.profile_picture = profile_picture
                    messages.success(request, '✅ Profile picture updated successfully!')
                else:
                    messages.error(request, 'Invalid file type. Please upload JPG, PNG, or GIF.')
        profile.save()
        messages.success(request, '✅ Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'profile.html', {'profile': profile})


# ============================================
# ADMIN VIEWS
# ============================================

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'staff_users': users.filter(is_staff=True).count(),
    }
    return render(request, 'admin_users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    reports = Report.objects.all()
    six_months_ago = timezone.now() - timedelta(days=180)
    
    context = {
        'total_reports': reports.count(),
        'pending_reports': reports.filter(status='pending').count(),
        'investigating_reports': reports.filter(status='investigating').count(),
        'resolved_reports': reports.filter(status='resolved').count(),
        'closed_reports': reports.filter(status='closed').count(),
        'total_users': User.objects.count(),
        'recent_reports': reports.order_by('-created_at')[:10],
        'reports_by_type': reports.values('incident_type').annotate(count=Count('id')),
        'reports_by_status': reports.values('status').annotate(count=Count('id')),
        'reports_by_month': reports.filter(created_at__gte=six_months_ago).extra(select={'month': "strftime('%Y-%m', created_at)"}).values('month').annotate(count=Count('id')).order_by('month'),
        'recent_activity': AdminLog.objects.order_by('-created_at')[:10],
        'unread_messages': SupportMessage.objects.filter(is_read=False).count(),
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    reports = Report.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter: reports = reports.filter(status=status_filter)
    if type_filter: reports = reports.filter(incident_type=type_filter)
    
    context = {
        'reports': reports,
        'current_status': status_filter,
        'current_type': type_filter,
        'status_choices': Report.STATUS_CHOICES,
        'incident_types': Report.INCIDENT_TYPES,
    }
    return render(request, 'admin_reports.html', context)


@login_required
@user_passes_test(is_admin)
def admin_report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_status':
            report.status = request.POST.get('status')
            report.save()
            AdminLog.objects.create(admin=request.user, action='status_change', report=report, description=f'Changed status to {report.status}')
            messages.success(request, f'Report status updated')
            
        elif action == 'change_priority':
            report.priority = request.POST.get('priority')
            report.save()
            messages.success(request, f'Report priority updated')
            
        elif action == 'assign':
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                assigned_user = User.objects.get(id=assigned_to_id)
                report.assigned_to = assigned_user
                report.save()
                if assigned_user.email:
                    send_report_assigned_notification(report, assigned_user, request.user)
                messages.success(request, f'Report assigned to {assigned_user.username}')
            else:
                report.assigned_to = None
                report.save()
                messages.info(request, 'Report unassigned')

        elif action == 'add_note':
            note = request.POST.get('admin_notes')
            if note:
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                report.admin_notes = f"{report.admin_notes}\n\n{timestamp} - {request.user.username}: {note}" if report.admin_notes else f"{timestamp} - {request.user.username}: {note}"
                report.save()
                messages.success(request, 'Note added successfully')

        return redirect('admin_report_detail', report_id=report_id)

    # Allow verified counselors and security to be assigned
    admins = User.objects.filter(profile__is_verified=True).exclude(id=request.user.id)
    
    context = {
        'report': report,
        'admins': admins,
        'status_choices': Report.STATUS_CHOICES,
    }
    return render(request, 'admin_report_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_users')
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'User {user.username} has been {"activated" if user.is_active else "deactivated"}.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_users')
    username = user.username
    user.delete()
    messages.success(request, f'User {username} has been permanently deleted.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_support_messages(request):
    messages_list = SupportMessage.objects.all().order_by('-created_at')
    return render(request, 'admin_support_messages.html', {'messages': messages_list, 'unread_count': messages_list.filter(is_read=False).count()})


@login_required
@user_passes_test(is_admin)
def admin_support_message_detail(request, message_id):
    msg = get_object_or_404(SupportMessage, id=message_id)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    
    if request.method == 'POST':
        response = request.POST.get('response')
        if response:
            msg.admin_response = response
            msg.is_read = True
            msg.save()
            if msg.user.email:
                send_counselor_response_notification(msg, request.user)
            messages.success(request, '✅ Response sent to user!')
            return redirect('admin_support_message_detail', message_id=message_id)
            
    return render(request, 'admin_support_message_detail.html', {'message': msg})


@login_required
@user_passes_test(is_admin)
def admin_resources(request):
    resources = Resource.objects.all().order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            Resource.objects.create(
                title=request.POST.get('title'), description=request.POST.get('description'),
                category=request.POST.get('category'), content=request.POST.get('content'),
                icon=request.POST.get('icon', 'fas fa-book'), link=request.POST.get('link', '')
            )
            messages.success(request, 'Resource added successfully!')
        return redirect('admin_resources')
    return render(request, 'admin_resources.html', {'resources': resources})


@login_required
@user_passes_test(is_admin)
def admin_delete_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    resource.delete()
    messages.success(request, 'Resource deleted.')
    return redirect('admin_resources')


@login_required
@user_passes_test(is_admin)
def admin_activity_log(request):
    logs = AdminLog.objects.all().order_by('-created_at')
    action_filter = request.GET.get('action')
    if action_filter: logs = logs.filter(action=action_filter)
    return render(request, 'admin_activity_log.html', {'logs': logs, 'action_filter': action_filter})


# ============================================
# COUNSELOR VIEWS
# ============================================

@login_required
def counselor_dashboard(request):
    try:
        profile = request.user.profile
        if profile.role != 'counselor' and not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        if not profile.is_verified and not request.user.is_superuser:
            messages.warning(request, 'Your account is pending verification.')
            return redirect('profile')
    except UserProfile.DoesNotExist:
        return redirect('dashboard')
    
    context = {
        'my_reports': Report.objects.filter(assigned_to=request.user).order_by('-created_at'),
        'pending_reports': Report.objects.filter(status__in=['pending', 'investigating'], assigned_to__isnull=True).order_by('-created_at'),
        'support_messages': SupportMessage.objects.filter(is_read=False).order_by('-created_at'),
    }
    return render(request, 'counselor_dashboard.html', context)


@login_required
def counselor_report_detail(request, report_id):
    try:
        profile = request.user.profile
        if profile.role != 'counselor' and not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        return redirect('dashboard')
    
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_status':
            old_status = report.status
            report.status = request.POST.get('status')
            report.save()
            if report.user.email: send_status_update_notification(report, old_status, report.status)
            messages.success(request, 'Status updated')
        elif action == 'add_note':
            note = request.POST.get('counselor_notes')
            if note:
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                report.admin_notes = f"{report.admin_notes}\n\n{timestamp} - {request.user.username} (Counselor): {note}" if report.admin_notes else f"{timestamp} - {request.user.username} (Counselor): {note}"
                report.save()
                messages.success(request, 'Note added')
        return redirect('counselor_report_detail', report_id=report_id)
        
    return render(request, 'counselor_report_detail.html', {'report': report, 'status_choices': Report.STATUS_CHOICES})


@login_required
@user_passes_test(is_admin)
def admin_verify_counselor(request, user_id):
    user = get_object_or_404(User, id=user_id)
    try:
        profile = user.profile
        profile.is_verified = True
        profile.save()
        messages.success(request, f'{user.username} has been verified.')
    except UserProfile.DoesNotExist:
        pass
    return redirect('admin_users')


@login_required
def counselor_reports(request):
    try:
        if request.user.profile.role != 'counselor' and not request.user.is_superuser: return redirect('dashboard')
    except UserProfile.DoesNotExist: return redirect('dashboard')
    return render(request, 'counselor_reports.html', {'reports': Report.objects.filter(assigned_to=request.user).order_by('-created_at')})


@login_required
def counselor_messages(request):
    try:
        if request.user.profile.role != 'counselor' and not request.user.is_superuser: return redirect('dashboard')
    except UserProfile.DoesNotExist: return redirect('dashboard')
    
    messages_list = SupportMessage.objects.all().order_by('-created_at')
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        response = request.POST.get('response')
        if message_id and response:
            msg = get_object_or_404(SupportMessage, id=message_id)
            ChatMessage.objects.create(support_thread=msg, sender=request.user, message=response)
            msg.is_read = True
            msg.save()
            if msg.user.email: send_counselor_response_notification(msg, request.user)
            messages.success(request, 'Response sent successfully!')
            return redirect(f'/counselor/messages/?selected={message_id}')
            
    selected_id = request.GET.get('selected')
    if selected_id:
        try:
            msg = SupportMessage.objects.get(id=selected_id)
            if not msg.is_read: msg.is_read = True; msg.save()
        except SupportMessage.DoesNotExist: pass

    return render(request, 'counselor_messages.html', {
        'messages': messages_list, 'selected_id': selected_id,
        'counselor_notification_count': messages_list.filter(is_read=False).count(),
    })


@login_required
def counselor_sessions(request):
    try:
        if request.user.profile.role != 'counselor' and not request.user.is_superuser: return redirect('dashboard')
    except UserProfile.DoesNotExist: return redirect('dashboard')
    return render(request, 'counselor_sessions.html')


@login_required
def counselor_upload_recording(request):
    try:
        if request.user.profile.role != 'counselor' and not request.user.is_superuser: return redirect('dashboard')
    except UserProfile.DoesNotExist: return redirect('dashboard')

    students = User.objects.filter(profile__role='student').order_by('first_name')
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        title = request.POST.get('title')
        notes = request.POST.get('notes')
        video_file = request.FILES.get('video_file')

        if student_id and title and video_file:
            SessionRecording.objects.create(
                student=get_object_or_404(User, id=student_id),
                counselor=request.user, title=title, notes=notes, video_file=video_file
            )
            messages.success(request, '✅ Session recording uploaded!')
            return redirect('counselor_upload_recording')
        else:
            messages.error(request, 'Please fill all fields and choose a video.')
            
    return render(request, 'counselor_upload_recording.html', {'students': students})


@login_required
def my_sessions(request):
    return render(request, 'my_sessions.html', {'recordings': SessionRecording.objects.filter(student=request.user).order_by('-date_recorded')})


# ============================================
# SECURITY VIEWS
# ============================================

@login_required
def security_dashboard(request):
    """Dashboard for security personnel"""
    try:
        profile = request.user.profile
        if profile.role != 'security' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Security area only.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        return redirect('dashboard')
    
    my_reports = Report.objects.filter(assigned_to=request.user).order_by('-created_at')
    urgent_reports = Report.objects.filter(status__in=['pending', 'investigating'], assigned_to__isnull=True).order_by('-created_at')
    
    context = {
        'urgent_reports': urgent_reports,
        'my_reports': my_reports,
    }
    return render(request, 'security_dashboard.html', context)


@login_required
def security_incident_detail(request, report_id):
    """Security view to handle a specific incident"""
    try:
        profile = request.user.profile
        if profile.role not in ['security', 'staff'] and not request.user.is_superuser:
            messages.error(request, 'Access denied. Security area only.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        return redirect('dashboard')
    
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_status':
            new_status = request.POST.get('status')
            report.status = new_status
            report.assigned_to = request.user
            report.save()
            messages.success(request, f'Incident status updated to {new_status}. You are now assigned to this case.')
        
        elif action == 'add_note':
            note = request.POST.get('officer_notes')
            if note:
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                if report.admin_notes:
                    report.admin_notes += f"\n\n{timestamp} - {request.user.username} (Security): {note}"
                else:
                    report.admin_notes = f"{timestamp} - {request.user.username} (Security): {note}"
                report.save()
                messages.success(request, 'Officer note added.')
        
        return redirect('security_incident_detail', report_id=report_id)

    context = {
        'report': report,
    }
    return render(request, 'security_incident_detail.html', context)


# ============================================
# CONTACT SUPPORT & PANIC VIEWS
# ============================================

def contact_support(request):
    """Public contact form to email the support team"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and message:
            try:
                send_mail(
                    subject=f"SafeCampus Contact: {subject}",
                    message=f"New message from {name} ({email}):\n\n{message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['support@safecampus.ac.za'], 
                    fail_silently=False,
                )
                messages.success(request, '✅ Your email has been sent to our support team!')
                return redirect('contact_support')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
        else:
            messages.error(request, 'Please fill in all fields.')
            
    return render(request, 'contact_support.html')


@login_required
def trigger_panic(request):
    """Silently alerts security via SMS without changing the user's screen"""
    if request.method == 'POST':
        try:
            # 1. Get the GPS location from the JavaScript request
            data = json.loads(request.body)
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            # 2. Format the location string
            if lat and lon:
                location_string = f"GPS Coordinates: {lat}, {lon}. Map: https://www.google.com/maps?q={lat},{lon}"
            else:
                location_string = "PANIC BUTTON ACTIVATED (GPS Location Unavailable - User Denied Permission)"
            
            # 3. Create the high-priority emergency report
            report = Report.objects.create(
                user=request.user,
                incident_type='other',
                priority='critical',
                status='pending',
                location=location_string,
                incident_date=timezone.now(),
                description='🚨 PANIC BUTTON ACTIVATED. User is in immediate danger. Please dispatch security immediately.'
            )
            
            # 4. Find all verified Security Officers and send them an SMS
            security_officers = User.objects.filter(profile__role='security', profile__is_verified=True)
            
            sms_sent_to = []
            
            for officer in security_officers:
                phone = officer.profile.phone_number # type: ignore
                if not phone:
                    continue
                    
                if phone.startswith('0'):
                    phone = '+27' + phone[1:]
                
                sms_message = f"URGENT SafeCampus: PANIC BUTTON activated by {request.user.get_full_name()}."
                if lat and lon:
                    sms_message += f" Location: {location_string}"
                sms_message += " URGENT! URGENT!,IMMEDIATE HELP NEEDED."
                
                # --- BULKSMS API INTEGRATION (JSON API) ---
                url = "https://api.bulksms.com/v1/messages"
                
                payload = {
                    "to": phone,
                    "body": sms_message
                }
                
                # ⚠️ REPLACE WITH YOUR REAL BULKSMS TOKEN ID AND SECRET
                BULKSMS_TOKEN_ID = "0B71BF014DDC4630B9B452FCC319801A-01-7"
                BULKSMS_TOKEN_SECRET = "iZudlAPWgo91Umdf#haI#pjClZub5"
                
                try:
                    response = requests.post(
                        url, 
                        json=payload, 
                        auth=HTTPBasicAuth(BULKSMS_TOKEN_ID, BULKSMS_TOKEN_SECRET),
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 201:
                        print(f"✅ REAL SMS SENT TO {officer.get_full_name()} at {phone}")
                        sms_sent_to.append(phone)
                    else:
                        print(f"❌ BULKSMS FAILED: Status {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"❌ BULKSMS CONNECTION ERROR: {str(e)}")
            
            print(f"🚨 PANIC BUTTON ACTIVATED BY {request.user.username} 🚨")
            return JsonResponse({'status': 'success', 'sms_sent': len(sms_sent_to), 'location': location_string})
            
        except Exception as e:
            print(f"Panic Error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'failed'}, status=400)

# ============================================
# PASSWORD RESET VIEWS
# ============================================

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import SetPasswordForm

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        users = User.objects.filter(email=email)
        
        if users.exists():
            user = users.first()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/password-reset/{uid}/{token}/')
            
            context = {
                'email_sent': True,
                'to_name': user.first_name or user.username, # type: ignore
                'to_email': email,
                'reset_link': reset_link,
                'service_id': 'service_72cezic',       
                'template_id': 'template_umyp2kf',     
                'public_key': 'jTyHz3WGGKqrZnPBb',     
            }
            return render(request, 'password_reset.html', context)
        else:
            messages.error(request, 'No account found with that email address.')
            
    return render(request, 'password_reset.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Your password has been reset successfully! Please log in.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('password_reset_request')