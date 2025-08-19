"""
Core throttling classes for API rate limiting.
"""

from rest_framework.throttling import UserRateThrottle


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