"""
Comprehensive security middleware for Django Personal Blog System.
Implements HTTPS enforcement, security headers, rate limiting, and audit logging.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation

from .models import AuditLog

User = get_user_model()
logger = logging.getLogger('security')


class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware that implements:
    - Security headers enforcement
    - IP blocking and rate limiting
    - Request validation and sanitization
    - Security monitoring and alerting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_config = getattr(settings, 'SECURITY_MONITORING', {})
        self.ip_security = getattr(settings, 'IP_SECURITY', {})
        self.security_headers = getattr(settings, 'SECURITY_HEADERS', {})
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request for security violations."""
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        request.client_ip = client_ip
        
        # Check IP blocking
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked request from IP: {client_ip}")
            return JsonResponse(
                {'error': 'Access denied'}, 
                status=403
            )
        
        # Check for suspicious activity
        if self._detect_suspicious_activity(request):
            self._handle_suspicious_activity(request)
        
        # Validate request headers
        if not self._validate_request_headers(request):
            logger.warning(f"Invalid headers from IP: {client_ip}")
            return JsonResponse(
                {'error': 'Invalid request'}, 
                status=400
            )
        
        # Check request size limits
        if not self._check_request_limits(request):
            logger.warning(f"Request size limit exceeded from IP: {client_ip}")
            return JsonResponse(
                {'error': 'Request too large'}, 
                status=413
            )
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        
        # Add security headers
        self._add_security_headers(response)
        
        # Log security events
        if hasattr(request, 'security_event'):
            self._log_security_event(request, response)
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if not self.ip_security.get('ENABLE_IP_BLOCKING', False):
            return False
        
        # Check whitelist
        whitelist = self.ip_security.get('WHITELIST_IPS', [])
        if ip in whitelist:
            return False
        
        # Check blacklist
        blacklist = self.ip_security.get('BLACKLIST_IPS', [])
        if ip in blacklist:
            return True
        
        # Check temporary blocks
        block_key = f"ip_blocked:{ip}"
        return cache.get(block_key, False)
    
    def _detect_suspicious_activity(self, request: HttpRequest) -> bool:
        """Detect suspicious activity patterns."""
        client_ip = request.client_ip
        
        # Check request frequency
        rate_key = f"request_rate:{client_ip}"
        current_requests = cache.get(rate_key, 0)
        
        threshold = self.ip_security.get('SUSPICIOUS_ACTIVITY_THRESHOLD', 10)
        if current_requests > threshold:
            return True
        
        # Check for common attack patterns
        suspicious_patterns = [
            'union select', 'script>', '<iframe', 'javascript:',
            '../', '..\\', '/etc/passwd', 'cmd.exe'
        ]
        
        request_data = str(request.GET) + str(request.POST) + str(request.path)
        for pattern in suspicious_patterns:
            if pattern.lower() in request_data.lower():
                return True
        
        return False
    
    def _handle_suspicious_activity(self, request: HttpRequest) -> None:
        """Handle detected suspicious activity."""
        client_ip = request.client_ip
        
        # Increment violation counter
        violation_key = f"security_violations:{client_ip}"
        violations = cache.get(violation_key, 0) + 1
        cache.set(violation_key, violations, 3600)  # 1 hour
        
        # Block IP if threshold exceeded
        max_violations = self.ip_security.get('MAX_FAILED_ATTEMPTS', 5)
        if violations >= max_violations:
            block_duration = self.ip_security.get('BLOCK_DURATION_MINUTES', 30) * 60
            block_key = f"ip_blocked:{client_ip}"
            cache.set(block_key, True, block_duration)
            
            logger.critical(f"IP {client_ip} blocked due to suspicious activity")
        
        # Log security event
        request.security_event = {
            'type': 'suspicious_activity',
            'ip': client_ip,
            'violations': violations,
            'details': f"Suspicious activity detected from {client_ip}"
        }
    
    def _validate_request_headers(self, request: HttpRequest) -> bool:
        """Validate request headers for security."""
        
        # Check User-Agent header
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) > 500:
            return False
        
        # Check for malicious headers
        malicious_headers = ['x-forwarded-host', 'x-original-url', 'x-rewrite-url']
        for header in malicious_headers:
            if request.META.get(f'HTTP_{header.upper().replace("-", "_")}'):
                logger.warning(f"Malicious header detected: {header}")
                return False
        
        return True
    
    def _check_request_limits(self, request: HttpRequest) -> bool:
        """Check request size and parameter limits."""
        
        # Check content length
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                length = int(content_length)
                max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 2621440)  # 2.5MB
                if length > max_size:
                    return False
            except ValueError:
                return False
        
        # Check parameter count
        total_params = len(request.GET) + len(request.POST)
        if total_params > 100:  # Reasonable limit
            return False
        
        return True
    
    def _add_security_headers(self, response: HttpResponse) -> None:
        """Add comprehensive security headers."""
        
        # Default security headers
        default_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
        }
        
        # Merge with configured headers
        headers = {**default_headers, **self.security_headers}
        
        for header, value in headers.items():
            if header not in response:
                response[header] = value
        
        # Add HSTS header for HTTPS
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)
            hsts_value = f'max-age={hsts_seconds}'
            
            if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
                hsts_value += '; includeSubDomains'
            
            if getattr(settings, 'SECURE_HSTS_PRELOAD', False):
                hsts_value += '; preload'
            
            response['Strict-Transport-Security'] = hsts_value
    
    def _log_security_event(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log security events for monitoring."""
        if not hasattr(request, 'security_event'):
            return
        
        event = request.security_event
        
        # Create audit log entry
        try:
            AuditLog.objects.create(
                user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                action_type=AuditLog.ActionType.SECURITY_EVENT,
                object_type='security',
                object_id=event.get('type', 'unknown'),
                details=event.get('details', ''),
                ip_address=event.get('ip', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                extra_data=event
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive request logging and monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> None:
        """Log incoming request details."""
        request.start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {getattr(request, 'client_ip', 'unknown')} "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}"
        )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response details and performance metrics."""
        
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"for {request.method} {request.path} "
                f"in {duration:.3f}s"
            )
            
            # Log slow requests
            if duration > 2.0:  # 2 seconds threshold
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.3f}s"
                )
        
        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive error handling and security.
    """
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """Handle exceptions securely."""
        
        # Log the exception
        logger.error(
            f"Exception in {request.method} {request.path}: {exception}",
            exc_info=True,
            extra={
                'request': request,
                'user': getattr(request, 'user', None),
                'ip': getattr(request, 'client_ip', 'unknown')
            }
        )
        
        # Don't expose sensitive information in production
        if not settings.DEBUG:
            return JsonResponse(
                {'error': 'Internal server error'},
                status=500
            )
        
        return None


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware for collecting analytics and usage statistics.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Collect analytics data."""
        
        # Skip analytics for certain paths
        skip_paths = ['/health/', '/metrics/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        # Collect basic metrics
        try:
            from apps.analytics.tasks import record_page_view
            
            # Record page view asynchronously
            record_page_view.delay(
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                user_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                ip_address=getattr(request, 'client_ip', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referer=request.META.get('HTTP_REFERER', ''),
                timestamp=timezone.now()
            )
        except Exception as e:
            logger.debug(f"Analytics collection failed: {e}")
        
        return response