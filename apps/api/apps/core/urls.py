"""
Core URLs for health checks and system endpoints.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Health check endpoints
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('ready/', views.ReadinessCheckView.as_view(), name='readiness_check'),
    path('alive/', views.LivenessCheckView.as_view(), name='liveness_check'),
]