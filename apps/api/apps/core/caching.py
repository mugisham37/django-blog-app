"""
API caching utilities and decorators.
"""

from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.response import Response
from rest_framework import status
import hashlib
import json
import pickle
from datetime import timedelta


class CacheKeyGenerator:
    """Generate consistent cache keys for API responses."""
    
    @staticmethod
    def generate_key(prefix, *args, **kwargs):
        """Generate a cache key from prefix and arguments."""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (str, int, float)):
                key_parts.append(f"{key}:{value}")
            else:
                key_parts.append(f"{key}:{hash(str(value))}")
        
        # Create hash of the key if it's too long
        key = "_".join(key_parts)
        if len(key) > 200:  # Redis key length limit
            key = hashlib.md5(key.encode()).hexdigest()
        
        return key
    
    @staticmethod
    def generate_view_key(view_name, request, *args, **kwargs):
        """Generate cache key for view responses."""
        key_parts = [
            'api_cache',
            view_name,
            request.method,
        ]
        
        # Add user information
        if request.user.is_authenticated:
            key_parts.append(f"user_{request.user.pk}")
        else:
            key_parts.append("anonymous")
        
        # Add query parameters
        if request.GET:
            query_hash = hashlib.md5(
                json.dumps(dict(request.GET), sort_keys=True).encode()
            ).hexdigest()
            key_parts.append(f"query_{query_hash}")
        
        # Add URL parameters
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            for key, value in sorted(kwargs.items()):
                key_parts.append(f"{key}_{value}")
        
        return "_".join(key_parts)


def cache_api_response(timeout=300, key_prefix=None, vary_on_user=True):
    """
    Decorator to cache API responses.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Custom prefix for cache key
        vary_on_user: Whether to include user in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Generate cache key
            view_name = key_prefix or f"{self.__class__.__name__}_{func.__name__}"
            
            if vary_on_user:
                cache_key = CacheKeyGenerator.generate_view_key(
                    view_name, request, *args, **kwargs
                )
            else:
                cache_key = CacheKeyGenerator.generate_key(
                    view_name, request.method, *args, **kwargs
                )
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response)
            
            # Execute view function
            response = func(self, request, *args, **kwargs)
            
            # Cache successful responses
            if response.status_code == status.HTTP_200_OK:
                cache.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator


def cache_queryset(timeout=300, key_prefix=None):
    """
    Decorator to cache queryset results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Custom prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            view_name = key_prefix or f"{self.__class__.__name__}_{func.__name__}"
            cache_key = CacheKeyGenerator.generate_key(view_name, *args, **kwargs)
            
            # Try to get from cache
            cached_queryset = cache.get(cache_key)
            if cached_queryset is not None:
                return cached_queryset
            
            # Execute function
            queryset = func(self, *args, **kwargs)
            
            # Cache the queryset (convert to list to avoid lazy evaluation issues)
            if queryset is not None:
                cache.set(cache_key, list(queryset), timeout)
            
            return queryset
        return wrapper
    return decorator


class CacheInvalidator:
    """Utility class for cache invalidation."""
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate all cache keys matching a pattern."""
        # This is a simplified version - in production, you might want to use
        # Redis SCAN command or maintain a registry of cache keys
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            # Get all keys matching pattern
            keys = redis_conn.keys(f"*{pattern}*")
            if keys:
                redis_conn.delete(*keys)
        except ImportError:
            # Fallback for non-Redis cache backends
            pass
    
    @staticmethod
    def invalidate_model_cache(model_name, instance_id=None):
        """Invalidate cache for a specific model."""
        if instance_id:
            pattern = f"{model_name}_{instance_id}"
        else:
            pattern = model_name
        
        CacheInvalidator.invalidate_pattern(pattern)
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a specific user."""
        pattern = f"user_{user_id}"
        CacheInvalidator.invalidate_pattern(pattern)
    
    @staticmethod
    def invalidate_view_cache(view_name):
        """Invalidate cache for a specific view."""
        CacheInvalidator.invalidate_pattern(view_name)


class SmartCacheMixin:
    """Mixin to add smart caching to ViewSets."""
    
    cache_timeout = 300  # 5 minutes default
    cache_per_user = True
    cache_safe_methods_only = True
    
    def get_cache_key(self, request, *args, **kwargs):
        """Generate cache key for the current request."""
        view_name = f"{self.__class__.__name__}_{self.action}"
        
        if self.cache_per_user:
            return CacheKeyGenerator.generate_view_key(
                view_name, request, *args, **kwargs
            )
        else:
            return CacheKeyGenerator.generate_key(
                view_name, request.method, *args, **kwargs
            )
    
    def should_cache_response(self, request, response):
        """Determine if response should be cached."""
        if self.cache_safe_methods_only and request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return False
        
        return response.status_code == status.HTTP_200_OK
    
    def get_cached_response(self, request, *args, **kwargs):
        """Get cached response if available."""
        cache_key = self.get_cache_key(request, *args, **kwargs)
        return cache.get(cache_key)
    
    def cache_response(self, request, response, *args, **kwargs):
        """Cache the response."""
        if self.should_cache_response(request, response):
            cache_key = self.get_cache_key(request, *args, **kwargs)
            cache.set(cache_key, response.data, self.cache_timeout)
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add caching logic."""
        # Check cache first
        cached_response = self.get_cached_response(request, *args, **kwargs)
        if cached_response is not None:
            return Response(cached_response)
        
        # Execute normal dispatch
        response = super().dispatch(request, *args, **kwargs)
        
        # Cache the response
        if isinstance(response, Response):
            self.cache_response(request, response, *args, **kwargs)
        
        return response


class ConditionalCacheMixin:
    """Mixin for conditional caching based on request parameters."""
    
    def should_use_cache(self, request):
        """Determine if cache should be used for this request."""
        # Don't cache if user explicitly requests fresh data
        if request.GET.get('no_cache') == '1':
            return False
        
        # Don't cache if user is staff and wants fresh data
        if request.user.is_staff and request.GET.get('fresh') == '1':
            return False
        
        return True
    
    def get_cache_timeout(self, request):
        """Get cache timeout based on request parameters."""
        # Allow custom timeout via query parameter
        custom_timeout = request.GET.get('cache_timeout')
        if custom_timeout and custom_timeout.isdigit():
            return int(custom_timeout)
        
        return getattr(self, 'cache_timeout', 300)


class ETagCacheMixin:
    """Mixin to add ETag support for caching."""
    
    def generate_etag(self, data):
        """Generate ETag from response data."""
        content = json.dumps(data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def check_etag(self, request, etag):
        """Check if client has current version."""
        client_etag = request.META.get('HTTP_IF_NONE_MATCH')
        return client_etag == etag
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Add ETag header to response."""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK and hasattr(response, 'data'):
            etag = self.generate_etag(response.data)
            response['ETag'] = etag
            
            # Check if client has current version
            if self.check_etag(request, etag):
                response.status_code = status.HTTP_304_NOT_MODIFIED
                response.data = None
        
        return response


# Decorator for method-level caching
def cache_method(timeout=300, key_func=None):
    """
    Decorator for caching method results.
    
    Args:
        timeout: Cache timeout in seconds
        key_func: Function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                cache_key = CacheKeyGenerator.generate_key(
                    f"{self.__class__.__name__}_{func.__name__}",
                    *args, **kwargs
                )
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute method
            result = func(self, *args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


# Cache warming utilities
class CacheWarmer:
    """Utility for warming up cache with frequently accessed data."""
    
    @staticmethod
    def warm_popular_posts():
        """Warm cache with popular posts."""
        from apps.blog.models import Post
        
        popular_posts = Post.objects.published().order_by('-view_count')[:10]
        
        for post in popular_posts:
            cache_key = f"post_detail_{post.slug}"
            # This would typically serialize the post data
            cache.set(cache_key, post, 3600)  # 1 hour
    
    @staticmethod
    def warm_categories():
        """Warm cache with category data."""
        from apps.blog.models import Category
        
        categories = Category.objects.filter(is_active=True)
        cache_key = "active_categories"
        cache.set(cache_key, list(categories), 3600)  # 1 hour
    
    @staticmethod
    def warm_user_data(user_id):
        """Warm cache with user-specific data."""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
            cache_key = f"user_profile_{user_id}"
            # Cache user profile data
            cache.set(cache_key, user, 1800)  # 30 minutes
        except User.DoesNotExist:
            pass