"""
Core throttling classes for API rate limiting.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, BaseThrottle
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import hashlib


class StaffRateThrottle(UserRateThrottle):
    """Rate throttling for staff users."""
    
    scope = 'staff'
    
    def allow_request(self, request, view):
        """Allow request if user is staff."""
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return super().allow_request(request, view)
        return True  # Don't throttle non-staff users with this throttle


class PremiumUserRateThrottle(UserRateThrottle):
    """Rate throttling for premium users."""
    
    scope = 'premium'
    
    def allow_request(self, request, view):
        """Allow request if user is premium."""
        if request.user and request.user.is_authenticated:
            # Check if user has premium role (you can customize this logic)
            if hasattr(request.user, 'role') and request.user.role == 'premium':
                return super().allow_request(request, view)
        return True  # Don't throttle non-premium users with this throttle


class BurstRateThrottle(UserRateThrottle):
    """Burst rate throttling for intensive operations."""
    
    scope = 'burst'


class SearchRateThrottle(BaseThrottle):
    """Rate throttling specifically for search operations."""
    
    scope = 'search'
    rate = '30/min'
    
    def get_cache_key(self, request, view):
        """Generate cache key for search throttling."""
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return f'throttle_search_{ident}'
    
    def allow_request(self, request, view):
        """Check if search request is allowed."""
        if not hasattr(view, 'action') or view.action != 'search':
            return True
            
        cache_key = self.get_cache_key(request, view)
        history = cache.get(cache_key, [])
        now = timezone.now()
        
        # Remove old entries
        history = [entry for entry in history if now - entry < timedelta(minutes=1)]
        
        if len(history) >= 30:  # 30 requests per minute
            return False
            
        history.append(now)
        cache.set(cache_key, history, 60)
        return True


class UploadRateThrottle(BaseThrottle):
    """Rate throttling for file upload operations."""
    
    scope = 'upload'
    rate = '10/min'
    
    def get_cache_key(self, request, view):
        """Generate cache key for upload throttling."""
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return f'throttle_upload_{ident}'
    
    def allow_request(self, request, view):
        """Check if upload request is allowed."""
        # Only throttle POST requests with files
        if request.method != 'POST' or not request.FILES:
            return True
            
        cache_key = self.get_cache_key(request, view)
        history = cache.get(cache_key, [])
        now = timezone.now()
        
        # Remove old entries
        history = [entry for entry in history if now - entry < timedelta(minutes=1)]
        
        if len(history) >= 10:  # 10 uploads per minute
            return False
            
        history.append(now)
        cache.set(cache_key, history, 60)
        return True


class IPBasedRateThrottle(AnonRateThrottle):
    """IP-based rate throttling with configurable rates."""
    
    def __init__(self):
        super().__init__()
        self.blocked_ips = cache.get('blocked_ips', set())
    
    def get_cache_key(self, request, view):
        """Generate cache key based on IP address."""
        ip = self.get_ident(request)
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            return f'throttle_blocked_{ip}'
            
        return f'throttle_ip_{ip}'
    
    def allow_request(self, request, view):
        """Check if request from this IP is allowed."""
        ip = self.get_ident(request)
        
        # Check if IP is permanently blocked
        if ip in self.blocked_ips:
            return False
            
        return super().allow_request(request, view)


class DynamicRateThrottle(BaseThrottle):
    """Dynamic rate throttling based on user type and endpoint."""
    
    def get_rate_for_user(self, user, view):
        """Get rate limit based on user type and view."""
        if not user.is_authenticated:
            return '100/hour'
        
        if user.is_staff:
            return '5000/hour'
        elif hasattr(user, 'role') and user.role == 'premium':
            return '2000/hour'
        else:
            return '1000/hour'
    
    def get_cache_key(self, request, view):
        """Generate cache key for dynamic throttling."""
        if request.user.is_authenticated:
            ident = f'user_{request.user.pk}'
        else:
            ident = f'anon_{self.get_ident(request)}'
        
        view_name = getattr(view, 'basename', view.__class__.__name__)
        return f'throttle_dynamic_{ident}_{view_name}'
    
    def parse_rate(self, rate):
        """Parse rate string into number and period."""
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)
    
    def allow_request(self, request, view):
        """Check if request is allowed based on dynamic rate."""
        rate = self.get_rate_for_user(request.user, view)
        num_requests, duration = self.parse_rate(rate)
        
        if num_requests is None:
            return True
        
        cache_key = self.get_cache_key(request, view)
        history = cache.get(cache_key, [])
        now = timezone.now()
        
        # Remove old entries
        cutoff = now - timedelta(seconds=duration)
        history = [entry for entry in history if entry > cutoff]
        
        if len(history) >= num_requests:
            return False
        
        history.append(now)
        cache.set(cache_key, history, duration)
        return True


class EndpointSpecificThrottle(BaseThrottle):
    """Endpoint-specific rate throttling."""
    
    # Define rates for specific endpoints
    ENDPOINT_RATES = {
        'login': '5/5min',
        'register': '3/5min',
        'password_reset': '3/10min',
        'comment_create': '10/min',
        'search': '30/min',
        'contact': '2/5min',
    }
    
    def get_endpoint_key(self, view):
        """Get endpoint key for rate limiting."""
        if hasattr(view, 'action'):
            return f"{view.basename}_{view.action}"
        return view.__class__.__name__.lower()
    
    def get_cache_key(self, request, view):
        """Generate cache key for endpoint throttling."""
        endpoint = self.get_endpoint_key(view)
        
        if request.user.is_authenticated:
            ident = f'user_{request.user.pk}'
        else:
            ident = f'anon_{self.get_ident(request)}'
        
        return f'throttle_endpoint_{endpoint}_{ident}'
    
    def parse_rate(self, rate):
        """Parse rate string into number and period."""
        if rate is None:
            return (None, None)
        
        parts = rate.split('/')
        num_requests = int(parts[0])
        
        if len(parts) == 1:
            duration = 60  # Default to 1 minute
        else:
            period = parts[1]
            if period.endswith('min'):
                duration = int(period[:-3]) * 60
            elif period.endswith('h'):
                duration = int(period[:-1]) * 3600
            elif period.endswith('d'):
                duration = int(period[:-1]) * 86400
            else:
                duration = int(period)
        
        return (num_requests, duration)
    
    def allow_request(self, request, view):
        """Check if request is allowed for this endpoint."""
        endpoint = self.get_endpoint_key(view)
        rate = self.ENDPOINT_RATES.get(endpoint)
        
        if not rate:
            return True  # No specific rate limit
        
        num_requests, duration = self.parse_rate(rate)
        
        if num_requests is None:
            return True
        
        cache_key = self.get_cache_key(request, view)
        history = cache.get(cache_key, [])
        now = timezone.now()
        
        # Remove old entries
        cutoff = now - timedelta(seconds=duration)
        history = [entry for entry in history if entry > cutoff]
        
        if len(history) >= num_requests:
            return False
        
        history.append(now)
        cache.set(cache_key, history, duration)
        return True