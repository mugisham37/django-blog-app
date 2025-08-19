"""
Unit tests for core mixins.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse
from django.views.generic import DetailView, ListView
from django.core.cache import cache
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from apps.core.mixins import (
    SEOMixin, CacheMixin, AnalyticsMixin, OwnershipMixin,
    PaginationMixin, BreadcrumbMixin
)


# Test models and views for mixin testing
class MockModel:
    """Mock model for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_absolute_url(self):
        return f"/test/{getattr(self, 'id', 1)}/"


class TestSEOView(SEOMixin, DetailView):
    """Test view using SEOMixin."""
    model = MockModel
    template_name = 'test.html'
    
    def get_object(self):
        return MockModel(
            id=1,
            title="Test Title",
            meta_title="Custom Meta Title",
            meta_description="Custom meta description",
            excerpt="Test excerpt for the post",
            content="<p>This is test content for the post.</p>",
            og_image=Mock(url="/media/test-image.jpg"),
            featured_image=Mock(url="/media/featured.jpg")
        )


class TestCacheView(CacheMixin, DetailView):
    """Test view using CacheMixin."""
    model = MockModel
    template_name = 'test.html'
    cache_timeout = 60
    
    def get_object(self):
        return MockModel(id=1, title="Test")


class TestAnalyticsView(AnalyticsMixin, DetailView):
    """Test view using AnalyticsMixin."""
    model = MockModel
    template_name = 'test.html'
    
    def get_object(self):
        return MockModel(id=1, title="Test")


class TestOwnershipView(OwnershipMixin, DetailView):
    """Test view using OwnershipMixin."""
    model = MockModel
    template_name = 'test.html'
    ownership_field = 'author'
    
    def get_object(self):
        return MockModel(id=1, author=self.request.user)


class SEOMixinTestCase(TestCase):
    """Test cases for SEOMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestSEOView()
        self.request = self.factory.get('/test/')
        self.view.request = self.request
        self.view.object = self.view.get_object()
    
    def test_get_meta_title_with_custom_meta_title(self):
        """Test meta title generation with custom meta_title."""
        meta_title = self.view.get_meta_title()
        self.assertEqual(meta_title, "Custom Meta Title")
    
    def test_get_meta_title_with_object_title(self):
        """Test meta title generation with object title."""
        self.view.object.meta_title = ""
        with patch.object(settings, 'SITE_NAME', 'Test Site'):
            meta_title = self.view.get_meta_title()
            self.assertEqual(meta_title, "Test Title | Test Site")
    
    def test_get_meta_title_default(self):
        """Test default meta title."""
        self.view.object = None
        with patch.object(settings, 'DEFAULT_META_TITLE', 'Default Title'):
            meta_title = self.view.get_meta_title()
            self.assertEqual(meta_title, 'Default Title')
    
    def test_get_meta_description_with_custom_description(self):
        """Test meta description with custom meta_description."""
        description = self.view.get_meta_description()
        self.assertEqual(description, "Custom meta description")
    
    def test_get_meta_description_with_excerpt(self):
        """Test meta description with excerpt."""
        self.view.object.meta_description = ""
        description = self.view.get_meta_description()
        self.assertEqual(description, "Test excerpt for the post")
    
    def test_get_meta_description_from_content(self):
        """Test meta description extracted from content."""
        self.view.object.meta_description = ""
        self.view.object.excerpt = ""
        description = self.view.get_meta_description()
        self.assertEqual(description, "This is test content for the post.")
    
    def test_get_og_image_with_custom_og_image(self):
        """Test OG image with custom og_image."""
        og_image = self.view.get_og_image()
        self.assertEqual(og_image, "/media/test-image.jpg")
    
    def test_get_og_image_with_featured_image(self):
        """Test OG image with featured_image fallback."""
        self.view.object.og_image = None
        og_image = self.view.get_og_image()
        self.assertEqual(og_image, "/media/featured.jpg")
    
    def test_get_canonical_url(self):
        """Test canonical URL generation."""
        canonical_url = self.view.get_canonical_url()
        self.assertEqual(canonical_url, "http://testserver/test/1/")
    
    def test_get_context_data(self):
        """Test context data includes SEO fields."""
        context = self.view.get_context_data()
        
        self.assertIn('meta_title', context)
        self.assertIn('meta_description', context)
        self.assertIn('og_image', context)
        self.assertIn('canonical_url', context)
        
        self.assertEqual(context['meta_title'], "Custom Meta Title")
        self.assertEqual(context['meta_description'], "Custom meta description")


class CacheMixinTestCase(TestCase):
    """Test cases for CacheMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestCacheView()
        cache.clear()  # Clear cache before each test
    
    def test_get_cache_key_basic(self):
        """Test basic cache key generation."""
        request = self.factory.get('/test/')
        self.view.request = request
        
        cache_key = self.view.get_cache_key()
        expected_parts = ['view', 'testcacheview', '/test/']
        
        for part in expected_parts:
            self.assertIn(part, cache_key)
    
    def test_get_cache_key_with_query_params(self):
        """Test cache key with query parameters."""
        request = self.factory.get('/test/?page=2&sort=title')
        self.view.request = request
        
        cache_key = self.view.get_cache_key()
        self.assertIn('view:testcacheview:/test/', cache_key)
    
    def test_get_cache_key_with_authenticated_user(self):
        """Test cache key with authenticated user."""
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        request = self.factory.get('/test/')
        request.user = user
        self.view.request = request
        
        cache_key = self.view.get_cache_key()
        self.assertIn(f'user_{user.id}', cache_key)
    
    def test_should_cache_anonymous_user(self):
        """Test caching for anonymous users."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        self.view.request = request
        
        self.assertTrue(self.view.should_cache())
    
    def test_should_not_cache_authenticated_user(self):
        """Test no caching for authenticated users by default."""
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        request = self.factory.get('/test/')
        request.user = user
        self.view.request = request
        
        self.assertFalse(self.view.should_cache())
    
    def test_should_not_cache_post_request(self):
        """Test no caching for POST requests."""
        request = self.factory.post('/test/')
        request.user = AnonymousUser()
        self.view.request = request
        
        self.assertFalse(self.view.should_cache())
    
    @patch('apps.core.mixins.cache')
    def test_cache_hit(self, mock_cache):
        """Test cache hit scenario."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        # Mock cache hit
        cached_response = HttpResponse("Cached content")
        mock_cache.get.return_value = cached_response
        
        self.view.request = request
        response = self.view.dispatch(request)
        
        self.assertEqual(response, cached_response)
        mock_cache.get.assert_called_once()
    
    @patch('apps.core.mixins.cache')
    def test_cache_miss_and_set(self, mock_cache):
        """Test cache miss and setting cache."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        self.view.request = request
        self.view.get_object = Mock(return_value=MockModel(id=1))
        
        with patch.object(self.view, 'render_to_response') as mock_render:
            mock_render.return_value = HttpResponse("New content")
            mock_render.return_value.status_code = 200
            
            response = self.view.dispatch(request)
            
            mock_cache.set.assert_called_once()
            self.assertEqual(response.content, b"New content")


class AnalyticsMixinTestCase(TestCase):
    """Test cases for AnalyticsMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestAnalyticsView()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
    
    def test_should_track_view_anonymous_user(self):
        """Test tracking for anonymous users."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        self.view.request = request
        
        self.assertTrue(self.view.should_track_view())
    
    def test_should_track_view_authenticated_user(self):
        """Test tracking for authenticated users."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        self.view.request = request
        
        self.assertTrue(self.view.should_track_view())
    
    def test_should_not_track_bots(self):
        """Test no tracking for bots."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request.META = {'HTTP_USER_AGENT': 'Googlebot/2.1'}
        self.view.request = request
        
        self.assertFalse(self.view.should_track_view())
    
    def test_should_not_track_authenticated_when_disabled(self):
        """Test no tracking for authenticated users when disabled."""
        self.view.track_authenticated_users = False
        
        request = self.factory.get('/test/')
        request.user = self.user
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        self.view.request = request
        
        self.assertFalse(self.view.should_track_view())
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test client IP extraction with X-Forwarded-For header."""
        request = self.factory.get('/test/')
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.view.request = request
        
        ip = self.view.get_client_ip()
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test client IP extraction without X-Forwarded-For header."""
        request = self.factory.get('/test/')
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        self.view.request = request
        
        ip = self.view.get_client_ip()
        self.assertEqual(ip, '127.0.0.1')
    
    @patch('apps.core.mixins.logger')
    def test_track_page_view_without_analytics_app(self, mock_logger):
        """Test page view tracking when analytics app is not available."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        request.META = {
            'HTTP_USER_AGENT': 'Mozilla/5.0',
            'HTTP_REFERER': 'http://example.com',
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.view.request = request
        
        self.view.track_page_view()
        
        # Should log the view when analytics app is not available
        mock_logger.info.assert_called_once()


class OwnershipMixinTestCase(TestCase):
    """Test cases for OwnershipMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestOwnershipView()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.other_user = User.objects.create_user('otheruser', 'other@example.com', 'password')
        self.staff_user = User.objects.create_user('staffuser', 'staff@example.com', 'password')
        self.staff_user.is_staff = True
        self.staff_user.save()
    
    def test_check_ownership_true(self):
        """Test ownership check returns True for owner."""
        obj = MockModel(author=self.user)
        request = self.factory.get('/test/')
        request.user = self.user
        self.view.request = request
        
        self.assertTrue(self.view.check_ownership(obj))
    
    def test_check_ownership_false(self):
        """Test ownership check returns False for non-owner."""
        obj = MockModel(author=self.other_user)
        request = self.factory.get('/test/')
        request.user = self.user
        self.view.request = request
        
        self.assertFalse(self.view.check_ownership(obj))
    
    def test_has_permission_unauthenticated(self):
        """Test permission denied for unauthenticated users."""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        self.view.request = request
        
        self.assertFalse(self.view.has_permission())
    
    def test_has_permission_staff_user(self):
        """Test permission granted for staff users."""
        obj = MockModel(author=self.other_user)
        request = self.factory.get('/test/')
        request.user = self.staff_user
        self.view.request = request
        
        self.assertTrue(self.view.has_permission(obj))
    
    def test_has_permission_owner(self):
        """Test permission granted for object owner."""
        obj = MockModel(author=self.user)
        request = self.factory.get('/test/')
        request.user = self.user
        self.view.request = request
        
        self.assertTrue(self.view.has_permission(obj))


class PaginationMixinTestCase(TestCase):
    """Test cases for PaginationMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        class TestPaginationView(PaginationMixin, ListView):
            model = MockModel
            template_name = 'test.html'
            
            def get_queryset(self):
                return [MockModel(id=i) for i in range(50)]
        
        self.view = TestPaginationView()
    
    def test_get_paginate_by_default(self):
        """Test default pagination."""
        request = self.factory.get('/test/')
        self.view.request = request
        
        paginate_by = self.view.get_paginate_by(None)
        self.assertEqual(paginate_by, 20)
    
    def test_get_paginate_by_custom(self):
        """Test custom pagination via GET parameter."""
        request = self.factory.get('/test/?per_page=10')
        self.view.request = request
        
        paginate_by = self.view.get_paginate_by(None)
        self.assertEqual(paginate_by, 10)
    
    def test_get_paginate_by_max_limit(self):
        """Test pagination max limit."""
        request = self.factory.get('/test/?per_page=200')
        self.view.request = request
        
        paginate_by = self.view.get_paginate_by(None)
        self.assertEqual(paginate_by, 100)  # Should be limited to 100
    
    def test_get_paginate_by_invalid_value(self):
        """Test pagination with invalid value."""
        request = self.factory.get('/test/?per_page=invalid')
        self.view.request = request
        
        paginate_by = self.view.get_paginate_by(None)
        self.assertEqual(paginate_by, 20)  # Should fall back to default


class BreadcrumbMixinTestCase(TestCase):
    """Test cases for BreadcrumbMixin."""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        class TestBreadcrumbView(BreadcrumbMixin, DetailView):
            model = MockModel
            template_name = 'test.html'
            breadcrumb_title = "Custom Title"
            
            def get_object(self):
                return MockModel(id=1, title="Test Object")
        
        self.view = TestBreadcrumbView()
    
    def test_get_breadcrumb_title_custom(self):
        """Test custom breadcrumb title."""
        title = self.view.get_breadcrumb_title()
        self.assertEqual(title, "Custom Title")
    
    def test_get_breadcrumb_title_from_object(self):
        """Test breadcrumb title from object."""
        self.view.breadcrumb_title = None
        self.view.object = MockModel(title="Object Title")
        
        title = self.view.get_breadcrumb_title()
        self.assertEqual(title, "Object Title")
    
    def test_get_breadcrumbs_basic(self):
        """Test basic breadcrumb generation."""
        breadcrumbs = self.view.get_breadcrumbs()
        
        self.assertEqual(len(breadcrumbs), 2)
        self.assertEqual(breadcrumbs[0]['title'], 'Home')
        self.assertEqual(breadcrumbs[0]['url'], '/')
        self.assertEqual(breadcrumbs[1]['title'], 'Custom Title')
        self.assertIsNone(breadcrumbs[1]['url'])
    
    def test_get_context_data_includes_breadcrumbs(self):
        """Test context data includes breadcrumbs."""
        request = self.factory.get('/test/')
        self.view.request = request
        
        context = self.view.get_context_data()
        self.assertIn('breadcrumbs', context)
        self.assertIsInstance(context['breadcrumbs'], list)