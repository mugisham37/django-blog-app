"""
API URL Configuration
Provides versioned API endpoints for the Django Personal Blog System.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'api'

urlpatterns = [
    # API Versions
    path('v1/', include('apps.api.v1.urls', namespace='v1')),
    path('v2/', include('apps.api.v2.urls', namespace='v2')),
    
    # Default to latest version
    path('', include('apps.api.v1.urls')),
]