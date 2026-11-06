# urls.py
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    # ===== HOME =====
    path('', views.home_view, name='home'),
    
    # ===== AUTHENTICATION =====
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # ===== USER DASHBOARD =====
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # ===== REPORTS =====
    path('new-report/', views.new_report_view, name='new_report'),
    path('reports/', views.reports_view, name='reports'),
    path('report/<int:report_id>/', views.report_detail_view, name='report_detail'),
    
    # ===== SUPPORT & RESOURCES =====
    path('support/', views.support_view, name='support'),
    path('resources/', views.resources_view, name='resources'),
    path('resource/<int:resource_id>/', views.resource_detail_view, name='resource_detail'),
    
    # ===== ADMIN URLs (Staff only) =====
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-report/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-toggle-user/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-support/', views.admin_support_messages, name='admin_support_messages'),
    
    # Added the missing detail view for admin messaging!
    path('admin-support/<int:message_id>/', views.admin_support_message_detail, name='admin_support_message_detail'),
    
    path('admin-resources/', views.admin_resources, name='admin_resources'),
    path('admin-delete-resource/<int:resource_id>/', views.admin_delete_resource, name='admin_delete_resource'),
    path('admin-activity-log/', views.admin_activity_log, name='admin_activity_log'),
    
    # ===== ROLE-SPECIFIC DASHBOARDS =====
    path('counselor/', views.counselor_dashboard, name='counselor_dashboard'),
    path('security/', views.security_dashboard, name='security_dashboard'),
    path('counselor/reports/', views.counselor_reports, name='counselor_reports'),
    path('counselor/messages/', views.counselor_messages, name='counselor_messages'),
    path('counselor/sessions/', views.counselor_sessions, name='counselor_sessions'),
    path('counselor/report/<int:report_id>/', views.counselor_report_detail, name='counselor_report_detail'),

    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('admin-verify-counselor/<int:user_id>/', views.admin_verify_counselor, name='admin_verify_counselor'),
    path('contact/', views.contact_support, name='contact_support'),
    path('admin-delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('counselor/upload-recording/', views.counselor_upload_recording, name='counselor_upload_recording'),
    path('my-sessions/', views.my_sessions, name='my_sessions'), # type: ignore
    path('security/incident/<int:report_id>/', views.security_incident_detail, name='security_incident_detail'),
    path('panic/', views.trigger_panic, name='trigger_panic'),
    # ===== API ENDPOINTS =====
    # This is where we plug in the router!
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)