"""
URL configuration for testing the database package.
"""

from django.urls import path
from django.http import HttpResponse

def health_check(request):
    """Simple health check view for testing."""
    return HttpResponse("OK")

urlpatterns = [
    path('health/', health_check, name='health_check'),
]