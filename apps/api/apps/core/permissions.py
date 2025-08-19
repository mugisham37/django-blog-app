"""
Custom permission classes for API access control.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.author == request.user or request.user.is_staff


class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission to only allow authors of a post to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to the author or staff
        if hasattr(obj, 'author'):
            return obj.author == request.user or request.user.is_staff
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        
        return request.user.is_staff


class IsStaffOrReadOnly(BasePermission):
    """
    Custom permission to only allow staff users to edit.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsPremiumUser(BasePermission):
    """
    Permission class for premium users.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user has premium role
        return (
            request.user.is_staff or 
            (hasattr(request.user, 'role') and request.user.role == 'premium')
        )


class IsVerifiedUser(BasePermission):
    """
    Permission class for verified users only.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is verified
        return (
            request.user.is_staff or 
            (hasattr(request.user, 'is_verified') and request.user.is_verified)
        )


class CanModerateComments(BasePermission):
    """
    Permission class for comment moderation.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_staff or 
            request.user.has_perm('comments.moderate_comment')
        )


class CanPublishPosts(BasePermission):
    """
    Permission class for publishing posts.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_staff or 
            request.user.has_perm('blog.publish_post')
        )


class RoleBasedPermission(BasePermission):
    """
    Role-based permission system.
    """
    
    # Define role hierarchy
    ROLE_HIERARCHY = {
        'admin': 100,
        'editor': 80,
        'author': 60,
        'premium': 40,
        'user': 20,
        'guest': 0,
    }
    
    # Define required roles for different actions
    ACTION_ROLES = {
        'create': ['author', 'editor', 'admin'],
        'update': ['author', 'editor', 'admin'],
        'delete': ['editor', 'admin'],
        'publish': ['editor', 'admin'],
        'moderate': ['editor', 'admin'],
        'admin': ['admin'],
    }
    
    def get_user_role(self, user):
        """Get user role with fallback."""
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'editor'
        elif hasattr(user, 'role'):
            return user.role
        elif user.is_authenticated:
            return 'user'
        else:
            return 'guest'
    
    def get_required_role_level(self, action):
        """Get minimum role level required for action."""
        required_roles = self.ACTION_ROLES.get(action, ['user'])
        return min(self.ROLE_HIERARCHY.get(role, 0) for role in required_roles)
    
    def has_permission(self, request, view):
        """Check if user has permission based on role."""
        user_role = self.get_user_role(request.user)
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        
        # Determine action from view
        action = getattr(view, 'action', 'read')
        if request.method in permissions.SAFE_METHODS:
            action = 'read'
        elif request.method == 'POST':
            action = 'create'
        elif request.method in ['PUT', 'PATCH']:
            action = 'update'
        elif request.method == 'DELETE':
            action = 'delete'
        
        required_level = self.get_required_role_level(action)
        return user_level >= required_level
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        # Allow read access to all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user_role = self.get_user_role(request.user)
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        
        # Owners can always edit their own content
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        elif hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check role-based permissions
        action = 'update' if request.method in ['PUT', 'PATCH'] else 'delete'
        required_level = self.get_required_role_level(action)
        
        return user_level >= required_level


class IPWhitelistPermission(BasePermission):
    """
    Permission class that allows access only from whitelisted IPs.
    """
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def has_permission(self, request, view):
        """Check if request IP is whitelisted."""
        from django.conf import settings
        
        # Get whitelisted IPs from settings
        whitelist = getattr(settings, 'IP_WHITELIST', [])
        
        if not whitelist:
            return True  # No whitelist configured
        
        client_ip = self.get_client_ip(request)
        return client_ip in whitelist


class TimeBasedPermission(BasePermission):
    """
    Permission class that restricts access based on time.
    """
    
    def has_permission(self, request, view):
        """Check if current time allows access."""
        from django.conf import settings
        
        # Get allowed time range from settings
        start_hour = getattr(settings, 'API_ACCESS_START_HOUR', 0)
        end_hour = getattr(settings, 'API_ACCESS_END_HOUR', 24)
        
        current_hour = timezone.now().hour
        
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:  # Overnight range
            return current_hour >= start_hour or current_hour < end_hour


class RateLimitedPermission(BasePermission):
    """
    Permission class that implements custom rate limiting.
    """
    
    def get_cache_key(self, request):
        """Generate cache key for rate limiting."""
        if request.user.is_authenticated:
            return f'rate_limit_user_{request.user.pk}'
        else:
            # Use IP for anonymous users
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return f'rate_limit_ip_{ip}'
    
    def has_permission(self, request, view):
        """Check if request is within rate limits."""
        cache_key = self.get_cache_key(request)
        
        # Get current request count
        current_count = cache.get(cache_key, 0)
        
        # Define limits based on user type
        if request.user.is_authenticated:
            if request.user.is_staff:
                limit = 1000  # Staff users get higher limits
            else:
                limit = 100   # Regular users
        else:
            limit = 50        # Anonymous users get lower limits
        
        if current_count >= limit:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, 3600)  # 1 hour window
        return True


class FeatureFlagPermission(BasePermission):
    """
    Permission class that checks feature flags.
    """
    
    def __init__(self, feature_name):
        self.feature_name = feature_name
    
    def has_permission(self, request, view):
        """Check if feature is enabled."""
        # This would integrate with your feature flag system
        # For now, we'll use a simple cache-based approach
        feature_key = f'feature_flag_{self.feature_name}'
        is_enabled = cache.get(feature_key, True)  # Default to enabled
        
        return is_enabled


class MaintenanceModePermission(BasePermission):
    """
    Permission class that blocks access during maintenance.
    """
    
    def has_permission(self, request, view):
        """Check if system is in maintenance mode."""
        maintenance_mode = cache.get('maintenance_mode', False)
        
        if maintenance_mode:
            # Allow staff users during maintenance
            return request.user.is_authenticated and request.user.is_staff
        
        return True


class APIKeyPermission(BasePermission):
    """
    Permission class for API key authentication.
    """
    
    def has_permission(self, request, view):
        """Check if valid API key is provided."""
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return False
        
        # Validate API key (this would typically check against a database)
        valid_keys = cache.get('valid_api_keys', set())
        return api_key in valid_keys


class ConditionalPermission(BasePermission):
    """
    Permission class that applies different permissions based on conditions.
    """
    
    def __init__(self, condition_func, permission_if_true, permission_if_false):
        self.condition_func = condition_func
        self.permission_if_true = permission_if_true
        self.permission_if_false = permission_if_false
    
    def has_permission(self, request, view):
        """Apply conditional permission logic."""
        if self.condition_func(request, view):
            return self.permission_if_true().has_permission(request, view)
        else:
            return self.permission_if_false().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """Apply conditional object permission logic."""
        if self.condition_func(request, view):
            return self.permission_if_true().has_object_permission(request, view, obj)
        else:
            return self.permission_if_false().has_object_permission(request, view, obj)