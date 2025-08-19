"""
API v2 URL Configuration
Future API version - currently mirrors v1
"""

from django.urls import path, include

app_name = 'v2'

urlpatterns = [
    # For now, v2 mirrors v1 - will be enhanced in future
    path('', include('apps.api.v1.urls')),
]