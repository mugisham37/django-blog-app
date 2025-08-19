"""
Enterprise Core Decorators Module

This module provides decorators for authentication, authorization, rate limiting,
security validation, and access logging.
"""

import json
import logging
import re
from functools import wraps
from typing import Optional, Callable, Any, Union
from datetime import datetime, timedelta

from .exceptions import (
    UserNotAuthenticatedException,
    InsufficientPermissionsException,
    RateLimitExceededException,
    XSSAttemptException,
    SuspiciousOperationException,
    get_client_ip
)

# Set up logging
security_logger = logging.getLogger('security')
access_logger = logging.getLogger('access')


def require_authentication(redirect_url: str = None, api_response: bool = False):
    """
    Decorator to require user authentication.
    
    Args:
        redirect_url: URL to redirect to if not authenticated
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.http import JsonResponse, HttpResponseRedirect
            from django.urls import reverse
            
            if not request.user.is_authenticated:
                if api_response or request.path.startswith('/api/'):
                    exception = UserNotAuthenticatedException()
                    return JsonResponse(
                        exception.to_dict(),
                        status=401
                    )
                else:
                    login_url = redirect_url or reverse('login')
                    return HttpResponseRedirect(login_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str, api_response: bool = False):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Permission string (e.g., 'blog.add_post')
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
            from django.urls import reverse
            
            if not request.user.is_authenticated:
                exception = UserNotAuthenticatedException()
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=401)
                else:
                    return HttpResponseRedirect(reverse('login'))
            
            if not request.user.has_perm(permission):
                user_permissions = list(request.user.get_all_permissions())
                exception = InsufficientPermissionsException(
                    required_permission=permission,
                    user_permissions=user_permissions
                )
                
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=403)
                else:
                    return HttpResponseForbidden("Insufficient permissions")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str, api_response: bool = False):
    """
    Decorator to require specific role (group membership).
    
    Args:
        role_name: Name of the required group/role
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
            from django.urls import reverse
            
            if not request.user.is_authenticated:
                exception = UserNotAuthenticatedException()
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=401)
                else:
                    return HttpResponseRedirect(reverse('login'))
            
            if not request.user.groups.filter(name=role_name).exists():
                user_groups = list(request.user.groups.values_list('name', flat=True))
                exception = InsufficientPermissionsException(
                    required_permission=f"Role: {role_name}",
                    user_permissions=user_groups
                )
                
                if api_response or request.path.startswith('/api/'):
                 tor


def require_staff(api_response: bool = False):
    """
    Decorator to require staff status.
    
    Args:
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                exception = UserNotAuthenticatedException()
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=401)
                else:
                    return HttpResponseRedirect(reverse('login'))
            
            if not request.user.is_staff:
                exception = InsufficientPermissionsException(
                    required_permission="Staff status"
                )
                
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=403)
                else:
                    return HttpResponseForbidden("Staff access required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_superuser(api_response: bool = False):
    """
    Decorator to require superuser status.
    
    Args:
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                exception = UserNotAuthenticatedException()
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=401)
                else:
                    return HttpResponseRedirect(reverse('login'))
            
            if not request.user.is_superuser:
                exception = InsufficientPermissionsException(
                    required_permission="Superuser status"
                )
                
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=403)
                else:
                    return HttpResponseForbidden("Superuser access required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_ownership(model_class, lookup_field: str = 'pk', 
                     owner_field: str = 'author', api_response: bool = False):
    """
    Decorator to require object ownership.
    
    Args:
        model_class: The model class to check ownership for
        lookup_field: Field to lookup the object
        owner_field: Field that contains the owner reference
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                exception = UserNotAuthenticatedException()
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=401)
                else:
                    return HttpResponseRedirect(reverse('login'))
            
            # Get the object
            lookup_value = kwargs.get(lookup_field)
            if not lookup_value:
                return HttpResponseForbidden("Object not found")
            
            try:
                obj = model_class.objects.get(**{lookup_field: lookup_value})
                owner = getattr(obj, owner_field, None)
                
                if owner != request.user and not request.user.is_staff:
                    exception = InsufficientPermissionsException(
                        required_permission="Object ownership"
                    )
                    
                    if api_response or request.path.startswith('/api/'):
                        return JsonResponse(exception.to_dict(), status=403)
                    else:
                        return HttpResponseForbidden("Access denied")
                
            except model_class.DoesNotExist:
                return HttpResponseForbidden("Object not found")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 60, per_user: bool = True, 
               api_response: bool = False):
    """
    Decorator to implement rate limiting.
    
    Args:
        requests_per_minute: Maximum requests per minute
        per_user: Whether to limit per user or per IP
        api_response: Whether to return JSON response for API endpoints
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Determine the key for rate limiting
            if per_user and request.user.is_authenticated:
                key = f"rate_limit_user_{request.user.id}_{view_func.__name__}"
            else:
                ip = get_client_ip(request)
                key = f"rate_limit_ip_{ip}_{view_func.__name__}"
            
            # Get current count
            current_count = cache.get(key, 0)
            
            if current_count >= requests_per_minute:
                exception = RateLimitExceededException(
                    limit_type=f"{view_func.__name__} requests",
                    retry_after=60
                )
                
                if api_response or request.path.startswith('/api/'):
                    return JsonResponse(exception.to_dict(), status=429)
                else:
                    return HttpResponseForbidden("Rate limit exceeded")
            
            # Increment counter
            cache.set(key, current_count + 1, 60)  # 60 seconds timeout
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def log_access(action: str, log_level: str = 'INFO'):
    """
    Decorator to log access to views.
    
    Args:
        action: Description of the action being logged
        log_level: Logging level (INFO, WARNING, ERROR)
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Prepare log data
            log_data = {
                'action': action,
                'view': view_func.__name__,
                'path': request.path,
                'method': request.method,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'timestamp': datetime.now().isoformat(),
            }
            
            if request.user.is_authenticated:
                log_data.update({
                    'user_id': request.user.id,
                    'username': request.user.username,
                })
            
            # Execute view
            response = view_func(request, *args, **kwargs)
            
            # Add response status to log
            log_data['status_code'] = response.status_code
            
            # Log the access
            log_message = f"Access logged: {action} by {log_data.get('username', 'anonymous')} from {log_data['ip_address']}"
            
            if log_level.upper() == 'WARNING':
                access_logger.warning(log_message, extra=log_data)
            elif log_level.upper() == 'ERROR':
                access_logger.error(log_message, extra=log_data)
            else:
                access_logger.info(log_message, extra=log_data)
            
            return response
        return wrapper
    return decorator


def detect_suspicious_activity(max_failed_attempts: int = 5, 
                             lockout_duration: int = 300):
    """
    Decorator to detect and prevent suspicious activity.
    
    Args:
        max_failed_attempts: Maximum failed attempts before lockout
        lockout_duration: Lockout duration in seconds
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = get_client_ip(request)
            lockout_key = f"lockout_{ip}"
            attempts_key = f"failed_attempts_{ip}"
            
            # Check if IP is locked out
            if cache.get(lockout_key):
                exception = SuspiciousOperationException(
                    operation="Multiple failed attempts",
                    ip_address=ip
                )
                
                security_logger.warning(
                    f"Blocked request from locked out IP: {ip}",
                    extra={'ip_address': ip, 'path': request.path}
                )
                
                return HttpResponseForbidden("Access temporarily blocked")
            
            # Execute view
            response = view_func(request, *args, **kwargs)
            
            # Check if this was a failed attempt
            if response.status_code in [401, 403]:
                failed_attempts = cache.get(attempts_key, 0) + 1
                cache.set(attempts_key, failed_attempts, lockout_duration)
                
                if failed_attempts >= max_failed_attempts:
                    # Lock out the IP
                    cache.set(lockout_key, True, lockout_duration)
                    
                    security_logger.warning(
                        f"IP locked out due to suspicious activity: {ip}",
                        extra={
                            'ip_address': ip,
                            'failed_attempts': failed_attempts,
                            'path': request.path
                        }
                    )
            else:
                # Reset failed attempts on successful request
                cache.delete(attempts_key)
            
            return response
        return wrapper
    return decorator


def validate_content_security(check_xss: bool = True, 
                            check_sql_injection: bool = True):
    """
    Decorator to validate content for security threats.
    
    Args:
        check_xss: Whether to check for XSS attempts
        check_sql_injection: Whether to check for SQL injection attempts
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check POST data for security threats
            if request.method == 'POST':
                for key, value in request.POST.items():
                    if isinstance(value, str):
                        if check_xss and _contains_xss(value):
                            exception = XSSAttemptException(
                                content=value,
                                field=key
                            )
                            
                            security_logger.warning(
                                f"XSS attempt detected from {get_client_ip(request)}",
                                extra={
                                    'ip_address': get_client_ip(request),
                                    'field': key,
                                    'content': value[:100]
                                }
                            )
                            
                            return JsonResponse(exception.to_dict(), status=400)
                        
                        if check_sql_injection and _contains_sql_injection(value):
                            security_logger.warning(
                                f"SQL injection attempt detected from {get_client_ip(request)}",
                                extra={
                                    'ip_address': get_client_ip(request),
                                    'field': key,
                                    'content': value[:100]
                                }
                            )
                            
                            return JsonResponse({
                                'error': 'SecurityException',
                                'message': 'Suspicious content detected'
                            }, status=400)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def cache_result(timeout: int = 300, key_prefix: str = None, 
                vary_on_user: bool = False):
    """
    Decorator to cache view results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        vary_on_user: Whether to vary cache by user
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or view_func.__name__]
            
            if vary_on_user and request.user.is_authenticated:
                key_parts.append(f"user_{request.user.id}")
            
            # Add URL parameters to key
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}_{v}" for k, v in kwargs.items()])
            
            cache_key = "_".join(key_parts)
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Execute view and cache result
            response = view_func(request, *args, **kwargs)
            
            # Only cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator


# Class-based view mixins
class AuthenticationRequiredMixin:
    """Mixin to require authentication for class-based views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin:
    """Mixin to require specific permission for class-based views."""
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        
        if self.permission_required and not request.user.has_perm(self.permission_required):
            return HttpResponseForbidden("Insufficient permissions")
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin:
    """Mixin to require staff status for class-based views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        
        if not request.user.is_staff:
            return HttpResponseForbidden("Staff access required")
        
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin:
    """Mixin to require superuser status for class-based views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        
        if not request.user.is_superuser:
            return HttpResponseForbidden("Superuser access required")
        
        return super().dispatch(request, *args, **kwargs)


class RateLimitMixin:
    """Mixin to add rate limiting to class-based views."""
    rate_limit_requests = 60
    rate_limit_per_user = True
    
    def dispatch(self, request, *args, **kwargs):
        # Apply rate limiting
        if self.rate_limit_per_user and request.user.is_authenticated:
            key = f"rate_limit_user_{request.user.id}_{self.__class__.__name__}"
        else:
            ip = get_client_ip(request)
            key = f"rate_limit_ip_{ip}_{self.__class__.__name__}"
        
        current_count = cache.get(key, 0)
        
        if current_count >= self.rate_limit_requests:
            return HttpResponseForbidden("Rate limit exceeded")
        
        cache.set(key, current_count + 1, 60)
        
        return super().dispatch(request, *args, **kwargs)


# Helper functions for security validation
def _contains_xss(content: str) -> bool:
    """
    Check if content contains potential XSS attacks.
    
    Args:
        content: Content to check
    
    Returns:
        True if XSS patterns are detected
    """
    if not content:
        return False
    
    content_lower = content.lower()
    
    # XSS patterns
    xss_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'document\.',
        r'window\.',
        r'eval\s*\(',
        r'alert\s*\(',
        r'confirm\s*\(',
        r'prompt\s*\(',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, content_lower):
            return True
    
    return False


def _contains_sql_injection(content: str) -> bool:
    """
    Check if content contains potential SQL injection attacks.
    
    Args:
        content: Content to check
    
    Returns:
        True if SQL injection patterns are detected
    """
    if not content:
        return False
    
    content_lower = content.lower()
    
    # SQL injection patterns
    sql_patterns = [
        r'\bselect\b.*\bfrom\b',
        r'\binsert\b.*\binto\b',
        r'\bupdate\b.*\bset\b',
        r'\bdelete\b.*\bfrom\b',
        r'\bdrop\b.*\btable\b',
        r'\bunion\b.*\bselect\b',
        r'\bor\b.*1\s*=\s*1',
        r'\band\b.*1\s*=\s*1',
        r'--',
        r'/\*.*\*/',
        r'\bexec\b',
        r'\bexecute\b',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, content_lower):
            return True
    
    return False


# Export all decorators and mixins
__all__ = [
    # Function decorators
    'require_authentication',
    'require_permission',
    'require_role',
    'require_staff',
    'require_superuser',
    'require_ownership',
    'rate_limit',
    'log_access',
    'detect_suspicious_activity',
    'validate_content_security',
    'cache_result',
    
    # Class-based view mixins
    'AuthenticationRequiredMixin',
    'PermissionRequiredMixin',
    'StaffRequiredMixin',
    'SuperuserRequiredMixin',
    'RateLimitMixin',
    
    # Helper functions
    '_contains_xss',
    '_contains_sql_injection',
]