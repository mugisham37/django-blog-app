"""
Analytics WebSocket routing
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/analytics/dashboard/$', consumers.AnalyticsDashboardConsumer.as_asgi()),
]