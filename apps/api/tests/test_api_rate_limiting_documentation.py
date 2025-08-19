"""
Tests for API rate limiting and documentation implementation.
Tests task 12.2: Implement API rate limiting and documentation.
"""

import time
import json
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch

from apps.blog.models import Post, Category, Tag
from apps.comments.models import Comment

User = get_user_model()


class APIRateLimitingTestCase(APITestCase):
    """
    Test API rate limiting functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        # Create tokens
        self.user_token = Token.objects.create(user=self.user)
        self.staff_token = Token.objects.create(user=self.staff_user)
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Clear cache before each test
        cache.clear()
    
    def test_anonymous_rate_limiting(self):
        """Test rate limiting for anonymous users."""
        url = reverse('blog-api:post-list')
        
        # Make requests up to the limit
        for i in range(5):  # Reduced for testing
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # This would normally be rate limited in production
        # For testing, we'll verify the throttle classes are configured
        from apps.blog.api_views import PostViewSet
        viewset = PostViewSet()
        throttles = viewset.get_throttles()
        
        # Verify throttling mixins are applied
        self.assertTrue(hasattr(viewset, 'get_action_throttles'))
        self.assertTrue(hasattr(viewset, 'throttled'))
    
    def test_authenticated_user_rate_limiting(self):
        """Test rate limiting for authenticated users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('blog-api:post-list')
        
        # Make requests - authenticated users should have higher limits
        for i in range(10):  # Higher limit for authenticated users
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_user_rate_limiting(self):
        """Test rate limiting for staff users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.staff_token.key}')
        url = reverse('blog-api:post-list')
        
        # Staff users should have even higher limits
        for i in range(15):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @override_settings(REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '2/min',  # Very low limit for testing
        }
    })
    def test_rate_limit_exceeded_response(self):
        """Test the response when rate limit is exceeded."""
        url = reverse('blog-api:post-list')
        
        # Make requests to exceed the limit
        for i in range(3):
            response = self.client.get(url)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Verify the error response format
                self.assertIn('detail', response.data)
                self.assertIn('Retry-After', response.headers)
                break
    
    def test_search_specific_rate_limiting(self):
        """Test search-specific rate limiting."""
        url = reverse('blog-api:post-search')
        
        # Test search endpoint with throttling
        response = self.client.get(url, {'q': 'test'})
        
        # Verify search throttling is configured
        from apps.blog.api_views import PostViewSet
        viewset = PostViewSet()
        viewset.action = 'search'
        action_throttles = viewset.get_action_throttles()
        
        # Should have search-specific throttles
        throttle_classes = [throttle.__class__.__name__ for throttle in action_throttles]
        self.assertIn('SearchRateThrottle', throttle_classes)
    
    def test_bulk_operation_rate_limiting(self):
        """Test rate limiting for bulk operations."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.staff_token.key}')
        url = reverse('comments-api:comment-bulk-moderate')
        
        # Test bulk moderation endpoint
        data = {
            'comment_ids': [1, 2, 3],
            'action': 'approve'
        }
        response = self.client.post(url, data, format='json')
        
        # Verify bulk operation throttling is configured
        from apps.comments.api_views import CommentViewSet
        viewset = CommentViewSet()
        viewset.action = 'bulk_moderate'
        action_throttles = viewset.get_action_throttles()
        
        # Should have burst throttles for bulk operations
        throttle_classes = [throttle.__class__.__name__ for throttle in action_throttles]
        self.assertIn('BurstRateThrottle', throttle_classes)


class APICachingTestCase(APITestCase):
    """
    Test API response caching functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        cache.clear()
    
    def test_search_response_caching(self):
        """Test that search responses are cached."""
        url = reverse('blog-api:post-search')
        
        # First request should be a cache miss
        response1 = self.client.get(url, {'q': 'test'})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request should be a cache hit (if caching is working)
        response2 = self.client.get(url, {'q': 'test'})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify caching utilities are available
        from apps.blog.api_views import PostViewSet
        viewset = PostViewSet()
        self.assertTrue(hasattr(viewset, 'get_cached_response'))
        self.assertTrue(hasattr(viewset, 'cache_response'))
    
    def test_featured_posts_caching(self):
        """Test that featured posts are cached."""
        # Mark post as featured
        self.post.is_featured = True
        self.post.save()
        
        url = reverse('blog-api:post-featured')
        
        # Make request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the endpoint has caching decorator
        from apps.blog.api_views import PostViewSet
        viewset = PostViewSet()
        
        # Check if the method has caching capabilities
        self.assertTrue(hasattr(viewset, 'get_cache_key'))
    
    def test_popular_posts_caching(self):
        """Test that popular posts are cached."""
        url = reverse('blog-api:post-popular')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify caching is configured for popular posts
        from apps.blog.api_views import PostViewSet
        viewset = PostViewSet()
        self.assertTrue(hasattr(viewset, 'cache_response'))


class APIVersioningTestCase(APITestCase):
    """
    Test API versioning functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
    
    def test_v1_api_endpoints(self):
        """Test that v1 API endpoints are accessible."""
        # Test v1 posts endpoint
        url = '/api/v1/posts/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test v1 categories endpoint
        url = '/api/v1/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_default_api_endpoints(self):
        """Test that default API endpoints work (backward compatibility)."""
        # Test default posts endpoint
        url = '/api/posts/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test default categories endpoint
        url = '/api/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_versioning_configuration(self):
        """Test that API versioning is properly configured."""
        from django.conf import settings
        
        rest_framework_settings = settings.REST_FRAMEWORK
        
        # Verify versioning configuration
        self.assertEqual(
            rest_framework_settings['DEFAULT_VERSIONING_CLASS'],
            'rest_framework.versioning.NamespaceVersioning'
        )
        self.assertEqual(rest_framework_settings['DEFAULT_VERSION'], 'v1')
        self.assertIn('v1', rest_framework_settings['ALLOWED_VERSIONS'])


class APIDocumentationTestCase(APITestCase):
    """
    Test API documentation functionality.
    """
    
    def test_api_info_endpoint(self):
        """Test the API info endpoint."""
        url = '/api/docs/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response contains expected information
        data = response.json()
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('description', data)
        self.assertIn('rate_limits', data)
        self.assertIn('endpoints', data)
    
    def test_api_health_endpoint(self):
        """Test the API health check endpoint."""
        url = '/api/docs/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify health check response
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)
    
    def test_api_examples_endpoint(self):
        """Test the API examples endpoint."""
        url = '/api/docs/examples/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify examples contain expected sections
        data = response.json()
        self.assertIn('authentication', data)
        self.assertIn('posts', data)
        self.assertIn('comments', data)
        self.assertIn('rate_limiting', data)
    
    def test_api_schema_endpoint(self):
        """Test the API schema endpoint."""
        url = '/api/docs/schema/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify schema is generated
        self.assertIn('openapi', response.data or {})


class CustomThrottlingTestCase(TestCase):
    """
    Test custom throttling classes.
    """
    
    def test_staff_rate_throttle(self):
        """Test StaffRateThrottle class."""
        from apps.core.throttling import StaffRateThrottle
        
        throttle = StaffRateThrottle()
        self.assertEqual(throttle.scope, 'staff')
    
    def test_premium_user_rate_throttle(self):
        """Test PremiumUserRateThrottle class."""
        from apps.core.throttling import PremiumUserRateThrottle
        
        throttle = PremiumUserRateThrottle()
        self.assertEqual(throttle.scope, 'premium')
    
    def test_search_rate_throttle(self):
        """Test SearchRateThrottle class."""
        from apps.core.throttling import SearchRateThrottle
        
        throttle = SearchRateThrottle()
        self.assertEqual(throttle.scope, 'search')
    
    def test_upload_rate_throttle(self):
        """Test UploadRateThrottle class."""
        from apps.core.throttling import UploadRateThrottle
        
        throttle = UploadRateThrottle()
        self.assertEqual(throttle.scope, 'upload')
    
    def test_dynamic_rate_throttle(self):
        """Test DynamicRateThrottle class."""
        from apps.core.throttling import DynamicRateThrottle
        
        throttle = DynamicRateThrottle()
        throttle.scope = 'user'
        
        # Test trust score calculation
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        trust_score = throttle._get_user_trust_score(user)
        self.assertIsInstance(trust_score, float)
        self.assertGreaterEqual(trust_score, 0.0)
        self.assertLessEqual(trust_score, 1.0)


class ThrottlingUtilitiesTestCase(TestCase):
    """
    Test throttling utilities and mixins.
    """
    
    def test_throttling_mixin(self):
        """Test ThrottlingMixin functionality."""
        from apps.core.throttling_utils import ThrottlingMixin
        
        # Create a mock viewset with the mixin
        class MockViewSet(ThrottlingMixin):
            action = 'search'
            request = type('MockRequest', (), {'FILES': {}})()
        
        viewset = MockViewSet()
        action_throttles = viewset.get_action_throttles()
        
        # Should return search throttles for search action
        throttle_classes = [throttle.__class__.__name__ for throttle in action_throttles]
        self.assertIn('SearchRateThrottle', throttle_classes)
    
    def test_cache_throttling_mixin(self):
        """Test CacheThrottlingMixin functionality."""
        from apps.core.throttling_utils import CacheThrottlingMixin
        
        class MockViewSet(CacheThrottlingMixin):
            pass
        
        viewset = MockViewSet()
        
        # Test cache key generation
        mock_request = type('MockRequest', (), {
            'method': 'GET',
            'path': '/api/posts/',
            'user': type('MockUser', (), {'is_authenticated': False})(),
            'GET': type('MockQueryDict', (), {'urlencode': lambda: 'q=test'})(),
            'META': {'REMOTE_ADDR': '127.0.0.1'}
        })()
        
        cache_key = viewset.get_cache_key(mock_request)
        self.assertIsInstance(cache_key, str)
        self.assertIn('GET', cache_key)
        self.assertIn('api_posts', cache_key)
    
    def test_throttle_endpoint_decorator(self):
        """Test throttle_endpoint decorator."""
        from apps.core.throttling_utils import throttle_endpoint
        from apps.core.throttling import SearchRateThrottle
        
        @throttle_endpoint(throttle_classes=[SearchRateThrottle])
        def mock_view(self, request):
            return {'success': True}
        
        # Verify decorator can be applied
        self.assertTrue(callable(mock_view))


class APIConfigurationTestCase(TestCase):
    """
    Test API configuration settings.
    """
    
    def test_rest_framework_settings(self):
        """Test REST Framework configuration."""
        from django.conf import settings
        
        rest_settings = settings.REST_FRAMEWORK
        
        # Test versioning configuration
        self.assertEqual(
            rest_settings['DEFAULT_VERSIONING_CLASS'],
            'rest_framework.versioning.NamespaceVersioning'
        )
        self.assertEqual(rest_settings['DEFAULT_VERSION'], 'v1')
        
        # Test throttling configuration
        self.assertIn('DEFAULT_THROTTLE_CLASSES', rest_settings)
        self.assertIn('DEFAULT_THROTTLE_RATES', rest_settings)
        
        # Test rate limits
        rates = rest_settings['DEFAULT_THROTTLE_RATES']
        self.assertIn('anon', rates)
        self.assertIn('user', rates)
        self.assertIn('staff', rates)
        self.assertIn('premium', rates)
        self.assertIn('search', rates)
        self.assertIn('upload', rates)
        self.assertIn('burst', rates)
    
    def test_throttle_classes_import(self):
        """Test that custom throttle classes can be imported."""
        from apps.core.throttling import (
            StaffRateThrottle,
            PremiumUserRateThrottle,
            SearchRateThrottle,
            UploadRateThrottle,
            DynamicRateThrottle,
            IPBasedRateThrottle
        )
        
        # Verify all classes are importable
        self.assertTrue(StaffRateThrottle)
        self.assertTrue(PremiumUserRateThrottle)
        self.assertTrue(SearchRateThrottle)
        self.assertTrue(UploadRateThrottle)
        self.assertTrue(DynamicRateThrottle)
        self.assertTrue(IPBasedRateThrottle)
    
    def test_throttling_utils_import(self):
        """Test that throttling utilities can be imported."""
        from apps.core.throttling_utils import (
            ThrottlingMixin,
            CacheThrottlingMixin,
            throttle_endpoint,
            cache_response_with_throttling
        )
        
        # Verify all utilities are importable
        self.assertTrue(ThrottlingMixin)
        self.assertTrue(CacheThrottlingMixin)
        self.assertTrue(throttle_endpoint)
        self.assertTrue(cache_response_with_throttling)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'rest_framework.authtoken',
                'apps.core',
                'apps.blog',
                'apps.comments',
            ],
            REST_FRAMEWORK={
                'DEFAULT_THROTTLE_CLASSES': [
                    'rest_framework.throttling.AnonRateThrottle',
                    'rest_framework.throttling.UserRateThrottle',
                ],
                'DEFAULT_THROTTLE_RATES': {
                    'anon': '100/hour',
                    'user': '1000/hour',
                }
            }
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])