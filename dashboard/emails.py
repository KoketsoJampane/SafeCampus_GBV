"""
Email notification utilities for SafeCampus
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags


def send_welcome_email(user):
    """Sent when a new user registers"""
    subject = 'Welcome to SafeCampus'
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0d2137; color: white; padding: 25px; text-align: center;">
            <h1 style="margin: 0;">SafeCampus</h1>
            <p style="margin: 5px 0 0; opacity: 0.8;">Sol Plaatje University</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #0d2137;">Welcome, {user.get_full_name() or user.username}!</h2>
            <p>Thank you for joining SafeCampus — a safe, confidential platform for our university community.</p>
            <p>You can now:</p>
            <ul>
                <li>Report incidents confidentially</li>
                <li>Access support from trained counselors</li>
                <li>Find educational resources</li>
                <li>Track your reports</li>
            </ul>
            <p style="margin-top: 25px;">
                <a href="{settings.SITE_URL}/login/" 
                   style="background: #c94a2a; color: white; padding: 12px 25px; 
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    Sign In to Your Account
                </a>
            </p>
            <p style="color: #6c7a89; font-size: 0.9rem; margin-top: 30px;">
                If you didn't create this account, please ignore this email.
            </p>
        </div>
        <div style="background: #eef4f8; padding: 20px; text-align: center; color: #6c7a89; font-size: 0.85rem;">
            SafeCampus — Your Safety Matters<br>
            Sol Plaatje University
        </div>
    </div>
    """
    
    send_mail(
        subject=subject,
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"📧 Welcome email sent to {user.email}")


def send_support_message_notification(counselor, support_message):
    """Sent to counselor when a user sends a support message"""
    subject = f'New Support Message: {support_message.subject}'
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0d2137; color: white; padding: 25px;">
            <h2 style="margin: 0;">New Support Message</h2>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p><strong>From:</strong> {support_message.user.get_full_name() or support_message.user.username}</p>
            <p><strong>Email:</strong> {support_message.user.email}</p>
            <p><strong>Subject:</strong> {support_message.subject}</p>
            <div style="background: white; padding: 20px; border-left: 4px solid #c94a2a; margin: 20px 0;">
                <p style="margin: 0; white-space: pre-wrap;">{support_message.message}</p>
            </div>
            <p>
                <a href="{settings.SITE_URL}/counselor/messages/" 
                   style="background: #c94a2a; color: white; padding: 12px 25px; 
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    View and Respond
                </a>
            </p>
        </div>
    </div>
    """
    
    send_mail(
        subject=subject,
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[counselor.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"📧 Support notification sent to counselor: {counselor.email}")


def send_counselor_response_notification(support_message, counselor):
    """Sent to user when counselor responds"""
    subject = f'Counselor Responded to: {support_message.subject}'
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #2d6a4f; color: white; padding: 25px;">
            <h2 style="margin: 0;">You Have a Response</h2>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p>Hi {support_message.user.get_full_name() or support_message.user.username},</p>
            <p>A counselor has responded to your message: <strong>{support_message.subject}</strong></p>
            <div style="background: white; padding: 20px; border-left: 4px solid #2d6a4f; margin: 20px 0;">
                <p style="margin: 0; color: #2d6a4f; font-weight: bold;">Counselor Response:</p>
                <p style="margin: 10px 0 0; white-space: pre-wrap;">{support_message.admin_response}</p>
            </div>
            <p>
                <a href="{settings.SITE_URL}/support/" 
                   style="background: #2d6a4f; color: white; padding: 12px 25px; 
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    View Full Response
                </a>
            </p>
            <p style="color: #6c7a89; font-size: 0.9rem;">
                Your privacy is protected. Only you and your counselor can see this conversation.
            </p>
        </div>
    </div>
    """
    
    send_mail(
        subject=subject,
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[support_message.user.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"📧 Response notification sent to user: {support_message.user.email}")


def send_report_assigned_notification(report, assigned_to, assigned_by):
    """Sent when a report is assigned to a counselor/security"""
    subject = f'New Report Assigned: #{report.id}'
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0d2137; color: white; padding: 25px;">
            <h2 style="margin: 0;">New Report Assigned to You</h2>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p>Hi {assigned_to.get_full_name() or assigned_to.username},</p>
            <p>A report has been assigned to you by <strong>{assigned_by.get_full_name() or assigned_by.username}</strong>.</p>
            <table style="width: 100%; margin: 20px 0;">
                <tr><td style="padding: 8px 0;"><strong>Report ID:</strong></td><td>#{report.id}</td></tr>
                <tr><td style="padding: 8px 0;"><strong>Type:</strong></td><td>{report.get_incident_type_display()}</td></tr>
                <tr><td style="padding: 8px 0;"><strong>Location:</strong></td><td>{report.location}</td></tr>
                <tr><td style="padding: 8px 0;"><strong>Status:</strong></td><td>{report.get_status_display()}</td></tr>
            </table>
            <p>
                <a href="{settings.SITE_URL}/counselor/report/{report.id}/" 
                   style="background: #c94a2a; color: white; padding: 12px 25px; 
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    View Report
                </a>
            </p>
        </div>
    </div>
    """
    
    send_mail(
        subject=subject,
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[assigned_to.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"📧 Assignment notification sent to: {assigned_to.email}")


def send_status_update_notification(report, old_status, new_status):
    """Sent to user when their report status changes"""
    subject = f'Report #{report.id} Status Updated'
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0d2137; color: white; padding: 25px;">
            <h2 style="margin: 0;">Your Report Has Been Updated</h2>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p>Hi {report.user.get_full_name() or report.user.username},</p>
            <p>The status of your report <strong>#{report.id}</strong> has been updated.</p>
            <div style="background: white; padding: 20px; border-left: 4px solid #c94a2a; margin: 20px 0;">
                <p style="margin: 0;"><strong>Previous status:</strong> {old_status}</p>
                <p style="margin: 5px 0 0;"><strong>New status:</strong> <span style="color: #c94a2a; font-weight: bold;">{new_status}</span></p>
            </div>
            <p>
                <a href="{settings.SITE_URL}/reports/" 
                   style="background: #c94a2a; color: white; padding: 12px 25px; 
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    View Your Report
                </a>
            </p>
            <p style="color: #6c7a89; font-size: 0.9rem;">
                Thank you for trusting SafeCampus. Your report is being handled with care.
            </p>
        </div>
    </div>
    """
    
    send_mail(
        subject=subject,
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[report.user.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"📧 Status update sent to: {report.user.email}")