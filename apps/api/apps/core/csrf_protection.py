"""
Enhanced CSRF protection for Django Personal Blog System.
Implements advanced CSRF protection with token rotation and validation.
"""

import hashlib
import hmac
import logging
import time
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

logger = logging.getLogger('security')


class EnhancedCSRFMiddleware(CsrfViewMiddleware):
    """
    Enhanced CSRF middleware with additional security features:
    - Token rotation
    - Rate limiting for CSRF failures
    - Enhanced logging
    - Custom validation rules
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.csrf_config = {
            'ROTATION_INTERVAL': getattr(settings, 'CSRF_TOKEN_ROTATION_INTERVAL', 3600),
            'MAX_FAILURES_PER_IP': 10,
            'FAILURE_WINDOW': 300,  # 5 minutes
            'ENABLE_DOUBLE_SUBMIT': True,
        }
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Enhanced CSRF token processing."""
        
        # Skip CSRF for exempt views
        if getattr(request, '_dont_enforce_csrf_checks', False):
            return None
        
        # Check CSRF failure rate limiting
        if self._is_csrf_rate_limited(request):
            logger.warning(f"CSRF rate limit exceeded for IP: {getattr(request, 'client_ip', 'unknown')}")
            return JsonResponse({'error': 'Too many CSRF failures'}, status=429)
        
        # Perform standard CSRF check
        response = super().process_request(request)
        
        # Log CSRF failures
        if response and response.status_code == 403:
            self._log_csrf_failure(request)
        
        return response
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Enhanced CSRF token response processing."""
        
        # Rotate CSRF token if needed
        if self._should_rotate_token(request):
            self._rotate_csrf_token(request, response)
        
        return super().process_response(request, response)
    
    def _is_csrf_rate_limited(self, request: HttpRequest) -> bool:
        """Check if IP is rate limited for CSRF failures."""
        client_ip = getattr(request, 'client_ip', 'unknown')
        failure_key = f"csrf_failures:{client_ip}"
        
        failures = cache.get(failure_key, 0)
        return failures >= self.csrf_config['MAX_FAILURES_PER_IP']
    
    def _log_csrf_failure(self, request: HttpRequest) -> None:
        """Log CSRF failure and update rate limiting."""
        client_ip = getattr(request, 'client_ip', 'unknown')
        
        # Log the failure
        logger.warning(
            f"CSRF failure from IP: {client_ip}, "
            f"Path: {request.path}, "
            f"Method: {request.method}, "
            f"Referer: {request.META.get('HTTP_REFERER', 'none')}"
        )
        
        # Update failure count
        failure_key = f"csrf_failures:{client_ip}"
        failures = cache.get(failure_key, 0) + 1
        cache.set(failure_key, failures, self.csrf_config['FAILURE_WINDOW'])
        
        # Create security event
        if not hasattr(request, 'security_event'):
            request.security_event = {
                'type': 'csrf_failure',
                'ip': client_ip,
                'failures': failures,
                'details': f"CSRF token validation failed for {request.path}"
            }
    
    def _should_rotate_token(self, request: HttpRequest) -> bool:
        """Determine if CSRF token should be rotated."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Check rotation interval
        last_rotation_key = f"csrf_rotation:{request.user.id}"
        last_rotation = cache.get(last_rotation_key, 0)
        
        return (time.time() - last_rotation) > self.csrf_config['ROTATION_INTERVAL']
    
    def _rotate_csrf_token(self, request: HttpRequest, response: HttpResponse) -> None:
        """Rotate CSRF token for authenticated user."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Generate new token
            new_token = get_random_string(32)
            
            # Update session
            request.session['csrftoken'] = new_token
            
            # Set cookie
            response.set_cookie(
                'csrftoken',
                new_token,
                max_age=getattr(settings, 'CSRF_COOKIE_AGE', 31449600),
                secure=getattr(settings, 'CSRF_COOKIE_SECURE', False),
                httponly=getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
                samesite=getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax')
            )
            
            # Update rotation timestamp
            rotation_key = f"csrf_rotation:{request.user.id}"
            cache.set(rotation_key, time.time(), 86400)  # 24 hours
            
            logger.info(f"CSRF token rotated for user: {request.user.id}")


class CSRFTokenMiddleware(MiddlewareMixin):
    """
    Middleware to ensure CSRF token is available in all responses.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Ensure CSRF token is available."""
        
        # Add CSRF token to JSON responses for AJAX requests
        if (response.get('Content-Type', '').startswith('application/json') and 
            hasattr(request, 'user') and request.user.is_authenticated):
            
            try:
                from django.middleware.csrf import get_token
                csrf_token = get_token(request)
                
                # Add token to response headers for AJAX
                response['X-CSRFToken'] = csrf_token
                
            except Exception as e:
                logger.debug(f"Failed to add CSRF token to response: {e}")
        
        return response


class CSRFTokenRotationMiddleware(MiddlewareMixin):
    """
    Middleware for automatic CSRF token rotation based on security events.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Check if token rotation is needed based on security events."""
        
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
        
        # Check for security events that require token rotation
        security_events = [
            'password_change',
            'email_change',
            'permission_change',
            'suspicious_activity'
        ]
        
        user_id = request.user.id
        for event in security_events:
            event_key = f"security_event:{event}:{user_id}"
            if cache.get(event_key):
                # Mark for token rotation
                request._rotate_csrf_token = True
                cache.delete(event_key)
                break
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Rotate token if marked for rotation."""
        
        if getattr(request, '_rotate_csrf_token', False):
            self._force_token_rotation(request, response)
        
        return response
    
    def _force_token_rotation(self, request: HttpRequest, response: HttpResponse) -> None:
        """Force CSRF token rotation."""
        try:
            from django.middleware.csrf import get_token
            
            # Clear existing token
            if hasattr(request, 'session'):
                request.session.pop('csrftoken', None)
            
            # Generate new token
            new_token = get_token(request)
            
            # Set new cookie
            response.set_cookie(
                'csrftoken',
                new_token,
                max_age=getattr(settings, 'CSRF_COOKIE_AGE', 31449600),
                secure=getattr(settings, 'CSRF_COOKIE_SECURE', False),
                httponly=getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
                samesite=getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax')
            )
            
            logger.info(f"CSRF token force-rotated for user: {request.user.id}")
            
        except Exception as e:
            logger.error(f"Failed to rotate CSRF token: {e}")


class DoubleSubmitCSRFMiddleware(MiddlewareMixin):
    """
    Implements double-submit cookie pattern for enhanced CSRF protection.
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Validate double-submit CSRF pattern."""
        
        # Skip for safe methods
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return None
        
        # Skip for exempt views
        if getattr(request, '_dont_enforce_csrf_checks', False):
            return None
        
        # Check double-submit pattern
        cookie_token = request.COOKIES.get('csrftoken')
        header_token = request.META.get('HTTP_X_CSRFTOKEN')
        
        if not cookie_token or not header_token:
            logger.warning(f"Missing CSRF tokens in double-submit check from IP: {getattr(request, 'client_ip', 'unknown')}")
            return JsonResponse({'error': 'CSRF token missing'}, status=403)
        
        if not constant_time_compare(cookie_token, header_token):
            logger.warning(f"CSRF token mismatch in double-submit check from IP: {getattr(request, 'client_ip', 'unknown')}")
            return JsonResponse({'error': 'CSRF token invalid'}, status=403)
        
        return None


def csrf_failure_handler(request: HttpRequest, reason: str = "") -> HttpResponse:
    """
    Custom CSRF failure handler with enhanced logging and security.
    """
    
    client_ip = getattr(request, 'client_ip', 'unknown')
    
    # Log detailed CSRF failure information
    logger.warning(
        f"CSRF failure: {reason} from IP: {client_ip}, "
        f"Path: {request.path}, "
        f"Method: {request.method}, "
        f"Referer: {request.META.get('HTTP_REFERER', 'none')}, "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'none')}"
    )
    
    # Create security event
    if not hasattr(request, 'security_event'):
        request.security_event = {
            'type': 'csrf_failure',
            'ip': client_ip,
            'reason': reason,
            'details': f"CSRF validation failed: {reason}"
        }
    
    # Return appropriate response
    if request.content_type == 'application/json':
        return JsonResponse(
            {
                'error': 'CSRF verification failed',
                'code': 'csrf_failure'
            },
            status=403
        )
    else:
        return HttpResponse(
            '<h1>403 Forbidden</h1><p>CSRF verification failed.</p>',
            status=403,
            content_type='text/html'
        )


# Utility functions for CSRF token management

def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    return get_random_string(32)


def validate_csrf_token(request: HttpRequest, token: str) -> bool:
    """Validate CSRF token against request."""
    try:
        from django.middleware.csrf import get_token
        expected_token = get_token(request)
        return constant_time_compare(token, expected_token)
    except Exception:
        return False


def rotate_user_csrf_token(user_id: int) -> None:
    """Mark user for CSRF token rotation on next request."""
    rotation_key = f"csrf_rotation_required:{user_id}"
    cache.set(rotation_key, True, 3600)  # 1 hour


def trigger_csrf_rotation_on_security_event(user_id: int, event_type: str) -> None:
    """Trigger CSRF token rotation due to security event."""
    event_key = f"security_event:{event_type}:{user_id}"
    cache.set(event_key, True, 3600)  # 1 hour
    
    logger.info(f"CSRF rotation triggered for user {user_id} due to {event_type}")