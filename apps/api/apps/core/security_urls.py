"""
URL configuration for security-related endpoints.
"""

from django.urls import path, include
from . import security_views

app_name = 'security'

urlpatterns = [
    # CSP reporting
    path('csp-report/', security_views.csp_report_endpoint, name='csp_report'),
    
    # Security dashboard and monitoring (API)
    path('api/dashboard/', security_views.security_dashboard, name='api_dashboard'),
    path('api/status/', security_views.security_status, name='api_status'),
    path('api/alerts/', security_views.security_alerts, name='api_alerts'),
    path('api/scan/', security_views.run_security_scan, name='api_scan'),
    path('api/test-alert/', security_views.test_security_alert, name='api_test_alert'),
    path('api/rate-limit/', security_views.rate_limit_info, name='api_rate_limit'),
    
    # Health check
    path('health/', security_views.health_check, name='health_check'),
    
    # Report download
    path('report/download/', security_views.security_report_download, name='report_download'),
]