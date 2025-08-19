"""
WebSocket JWT Authentication Middleware
"""

import jwt
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.conf import settings
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token."""
    try:
        # Validate and decode the token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Get user from database
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """JWT Authentication middleware for WebSocket connections."""
    
    async def __call__(self, scope, receive, send):
        # Get token from query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        token = None
        if 'token' in query_params:
            token = query_params['token'][0]
        
        # Get user from token
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """WebSocket middleware stack with JWT authentication."""
    return JWTAuthMiddleware(inner)