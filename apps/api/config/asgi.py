"""
ASGI config for personal blog project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from apps.core.websocket_auth import JWTAuthMiddlewareStack
from apps.analytics.routing import websocket_urlpatterns as analytics_websocket_urlpatterns
from apps.blog.routing import websocket_urlpatterns as blog_websocket_urlpatterns
from apps.core.routing import websocket_urlpatterns as core_websocket_urlpatterns

# Combine all WebSocket URL patterns
websocket_urlpatterns = (
    analytics_websocket_urlpatterns + 
    blog_websocket_urlpatterns + 
    core_websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})