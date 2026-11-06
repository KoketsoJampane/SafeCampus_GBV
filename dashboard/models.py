from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Report(models.Model):
    INCIDENT_TYPES = [
        ('harassment', 'Harassment'),
        ('assault', 'Assault'),
        ('bullying', 'Bullying'),
        ('discrimination', 'Discrimination'),
        ('sexual_harassment', 'Sexual Harassment'),
        ('physical_abuse', 'Physical Abuse'),
        ('verbal_abuse', 'Verbal Abuse'),
        ('stalking', 'Stalking'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    location = models.CharField(max_length=200)
    incident_date = models.DateTimeField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_anonymous = models.BooleanField(default=False)
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.incident_type} - {self.created_at.strftime('%Y-%m-%d')}"

class SupportMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_messages')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)              # Counselor read the message
    is_read_by_user = models.BooleanField(default=False)      # 👈 User read the response
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subject}"
    

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fas fa-file-alt')
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff Member'),
        ('counselor', 'Counselor / Psychologist'),
        ('security', 'Security'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')  # <-- NEW
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_verified = models.BooleanField(default=False)
    qualification_doc = models.FileField(upload_to='qualifications/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}" # type: ignore
class ChatMessage(models.Model):
    support_thread = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:20]}"
class AdminLog(models.Model):
    """Track admin actions"""
    ACTION_TYPES = [
        ('assign', 'Assigned Report'),
        ('status_change', 'Status Changed'),
        ('resolve', 'Resolved Report'),
        ('comment', 'Added Comment'),
        ('user_block', 'User Blocked'),
        ('user_unblock', 'User Unblocked'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_logs')
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, null=True, blank=True)
    user_affected = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='affected_logs')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): # type: ignore
        return f"{self.admin.username} - {self.action} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class SessionRecording(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_recordings')
    counselor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='counselor_recordings')
    title = models.CharField(max_length=200)
    date_recorded = models.DateTimeField(auto_now_add=True)
    # Changed from URLField to FileField for uploads
    video_file = models.FileField(upload_to='session_recordings/', blank=True, null=True) 
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.title}"