"""
Tests for rate limiting and CSRF protection implementation.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.contrib.auth.models import Group

from apps.core.rate_limiting import (
    RateLimiter, RateLimitConfig, IPBlocklist, FailedAttemptTracker,
    rate_limit_view, check_ip_blocklist, track_failed_attempts
)
from apps.core.csrf_protection import (
    EnhancedCSRFMiddleware, csrf_protect_ajax, validate_csrf_for_api
)
from apps.core.exceptions import RateLimitExceededException, CSRFException

User = get_user_model()


class RateLimiterTestCase(TestCase):
    """Test cases for RateLimiter class."""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        key = "test_key"
        limit = 5
        window = 60
        
        # First 5 requests should pass
        for i in range(5):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(key, limit, window)
            self.assertFalse(is_limited)
            self.assertEqual(rate_info['remaining'], limit - i - 1)
        
        # 6th request should be rate limited
        is_limited, rate_info = self.rate_limiter.is_rate_limited(key, limit, window)
        self.assertTrue(is_limited)
        self.assertEqual(rate_info['remaining'], 0)
    
    def test_rate_limiter_sliding_window(self):
        """Test sliding window algorithm."""
        key = "test_sliding"
        limit = 3
        window = 2  # 2 seconds
        
        # Make 3 requests
        for i in range(3):
            is_limited, _ = self.rate_limiter.is_rate_limited(key, limit, window)
            self.assertFalse(is_limited)
        
        # 4th request should be limited
        is_limited, _ = self.rate_limiter.is_rate_limited(key, limit, window)
        self.assertTrue(is_limited)
        
        # Wait for window to pass
        time.sleep(2.1)
        
        # Should be able to make requests again
        is_limited, _ = self.rate_limiter.is_rate_limited(key, limit, window)
        self.assertFalse(is_limited)
    
    def test_rate_limit_key_generation(self):
        """Test rate limit key generation."""
        client = Client()
        request = client.get('/').wsgi_request
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.id = 123
        
        # Test user-based key
        key = self.rate_limiter.get_rate_limit_key(request, 'user', 'test_scope')
        self.assertIn('user:123', key)
        self.assertIn('test_scope', key)
        
        # Test IP-based key
        key = self.rate_limiter.get_rate_limit_key(request, 'ip', 'test_scope')
        self.assertIn('ip:', key)
        self.assertIn('test_scope', key)
    
    def test_clear_rate_limit(self):
        """Test clearing rate limits."""
        key = "test_clear"
        limit = 2
        window = 60
        
        # Exhaust rate limit
        for i in range(2):
            self.rate_limiter.is_rate_limited(key, limit, window)
        
        is_limited, _ = self.rate_limiter.is_rate_limited(key, limit, window)
        self.assertTrue(is_limited)
        
        # Clear rate limit
        self.rate_limiter.clear_rate_limit(key)
        
        # Should be able to make requests again
        is_limited, _ = self.rate_limiter.is_rate_limited(key, limit, window)
        self.assertFalse(is_limited)


class RateLimitConfigTestCase(TestCase):
    """Test cases for RateLimitConfig class."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_anonymous_user_limits(self):
        """Test rate limits for anonymous users."""
        config = RateLimitConfig.get_limit_for_user(None)
        self.assertEqual(config['limit'], 100)
        self.assertEqual(config['window'], 60)
    
    def test_authenticated_user_limits(self):
        """Test rate limits for authenticated users."""
        config = RateLimitConfig.get_limit_for_user(self.user)
        self.assertEqual(config['limit'], 300)
        self.assertEqual(config['window'], 60)
    
    def test_role_based_limits(self):
        """Test role-based rate limits."""
        # Create author group
        author_group = Group.objects.create(name='author')
        self.user.groups.add(author_group)
        
        config = RateLimitConfig.get_limit_for_user(self.user)
        self.assertEqual(config['limit'], 500)
        self.assertEqual(config['window'], 60)
    
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limits."""
        config = RateLimitConfig.get_limit_for_user(self.user, 'login')
        self.assertEqual(config['limit'], 5)
        self.assertEqual(config['window'], 300)


class IPBlocklistTestCase(TestCase):
    """Test cases for IPBlocklist class."""
    
    def setUp(self):
        self.ip_blocklist = IPBlocklist()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_block_and_check_ip(self):
        """Test blocking and checking IP addresses."""
        ip = "192.168.1.100"
        
        # IP should not be blocked initially
        self.assertFalse(self.ip_blocklist.is_blocked(ip))
        
        # Block the IP
        self.ip_blocklist.block_ip(ip, duration=60, reason="Test block")
        
        # IP should now be blocked
        self.assertTrue(self.ip_blocklist.is_blocked(ip))
    
    def test_unblock_ip(self):
        """Test unblocking IP addresses."""
        ip = "192.168.1.101"
        
        # Block and verify
        self.ip_blocklist.block_ip(ip, duration=60)
        self.assertTrue(self.ip_blocklist.is_blocked(ip))
        
        # Unblock and verify
        self.ip_blocklist.unblock_ip(ip)
        self.assertFalse(self.ip_blocklist.is_blocked(ip))


class FailedAttemptTrackerTestCase(TestCase):
    """Test cases for FailedAttemptTracker class."""
    
    def setUp(self):
        self.tracker = FailedAttemptTracker()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_record_failed_attempt(self):
        """Test recording failed attempts."""
        identifier = "192.168.1.102"
        
        # Record failed attempts
        for i in range(3):
            self.tracker.record_failed_attempt(identifier, 'login')
        
        # Check attempt count
        attempts = self.tracker.get_failed_attempts(identifier, 'login')
        self.assertEqual(attempts, 3)
    
    def test_clear_failed_attempts(self):
        """Test clearing failed attempts."""
        identifier = "192.168.1.103"
        
        # Record attempts
        self.tracker.record_failed_attempt(identifier, 'login')
        self.assertEqual(self.tracker.get_failed_attempts(identifier, 'login'), 1)
        
        # Clear attempts
        self.tracker.clear_failed_attempts(identifier, 'login')
        self.assertEqual(self.tracker.get_failed_attempts(identifier, 'login'), 0)
    
    @patch('apps.core.rate_limiting.IPBlocklist.block_ip')
    def test_auto_block_after_threshold(self, mock_block_ip):
        """Test automatic IP blocking after threshold."""
        identifier = "192.168.1.104"
        
        # Record 10 failed attempts (threshold)
        for i in range(10):
            self.tracker.record_failed_attempt(identifier, 'login')
        
        # Should have called block_ip
        mock_block_ip.assert_called_once()


class RateLimitDecoratorTestCase(TestCase):
    """Test cases for rate limiting decorators."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_rate_limit_decorator_basic(self):
        """Test basic rate limit decorator functionality."""
        @rate_limit_view(limit=2, window=60)
        def test_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        # Create mock request
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # First 2 requests should pass
        for i in range(2):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # 3rd request should be rate limited
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_decorator_api_response(self):
        """Test rate limit decorator with API response."""
        @rate_limit_view(limit=1, window=60, api_response=True)
        def test_api_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        request = self.client.get('/api/test/').wsgi_request
        request.user = self.user
        
        # First request should pass
        response = test_api_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Second request should be rate limited with JSON response
        response = test_api_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('application/json', response.get('Content-Type', ''))


class CSRFProtectionTestCase(TestCase):
    """Test cases for CSRF protection."""
    
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        request = self.client.get('/').wsgi_request
        token = get_token(request)
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)
    
    def test_csrf_protect_ajax_decorator(self):
        """Test CSRF protection for AJAX requests."""
        @csrf_protect_ajax
        def test_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        # Create request without CSRF token
        request = self.client.post('/test/', {}).wsgi_request
        request.user = self.user
        
        # Should fail CSRF validation
        response = test_view(request)
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_api_validation(self):
        """Test CSRF validation for API endpoints."""
        @validate_csrf_for_api
        def test_api_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        # GET request should pass (safe method)
        request = self.client.get('/api/test/').wsgi_request
        response = test_api_view(request)
        self.assertEqual(response.status_code, 200)
        
        # POST request without token should fail
        request = self.client.post('/api/test/', {}).wsgi_request
        response = test_api_view(request)
        self.assertEqual(response.status_code, 403)


class SecurityViewsTestCase(TestCase):
    """Test cases for security views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_get_csrf_token_view(self):
        """Test CSRF token retrieval view."""
        response = self.client.get('/core/security/csrf-token/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('csrf_token', data)
        self.assertIsNotNone(data['csrf_token'])
    
    def test_security_status_view_authenticated(self):
        """Test security status view for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/core/security/status/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('security_status', data)
        self.assertIn('rate_limit', data['security_status'])
        self.assertIn('csrf_token', data['security_status'])
    
    def test_security_status_view_anonymous(self):
        """Test security status view for anonymous users."""
        response = self.client.get('/core/security/status/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_report_security_incident(self):
        """Test security incident reporting."""
        incident_data = {
            'type': 'csrf_failure',
            'details': {
                'url': '/test/',
                'timestamp': '2023-01-01T00:00:00Z'
            }
        }
        
        response = self.client.post(
            '/core/security/report-incident/',
            data=json.dumps(incident_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_security_headers_test(self):
        """Test security headers test endpoint."""
        response = self.client.get('/core/security/headers-test/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('security_info', data)
        self.assertIn('csrf_token_present', data['security_info'])


class SecurityMiddlewareTestCase(TestCase):
    """Test cases for security middleware."""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_suspicious_request_detection(self):
        """Test detection of suspicious requests."""
        # Test with suspicious URL pattern
        response = self.client.get('/test/?q=<script>alert(1)</script>')
        # Should be blocked by security middleware
        self.assertIn(response.status_code, [400, 403])
    
    def test_rate_limiting_middleware(self):
        """Test rate limiting in middleware."""
        # Make many requests quickly
        responses = []
        for i in range(150):  # Exceed anonymous limit
            response = self.client.get('/')
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        self.assertIn(429, responses)
    
    def test_ip_blocking_middleware(self):
        """Test IP blocking in middleware."""
        from apps.core.rate_limiting import IPBlocklist
        
        ip_blocklist = IPBlocklist()
        ip_blocklist.block_ip('127.0.0.1', duration=60, reason='Test block')
        
        # Request should be blocked
        response = self.client.get('/')
        self.assertEqual(response.status_code, 403)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
)
class IntegrationTestCase(TestCase):
    """Integration tests for rate limiting and CSRF protection."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_rate_limiting_with_csrf_protection(self):
        """Test rate limiting combined with CSRF protection."""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Get CSRF token
        csrf_response = self.client.get('/core/security/csrf-token/')
        csrf_token = csrf_response.json()['csrf_token']
        
        # Make rate-limited requests with CSRF token
        responses = []
        for i in range(10):
            response = self.client.post(
                '/core/security/csrf-token/refresh/',
                HTTP_X_CSRFTOKEN=csrf_token
            )
            responses.append(response.status_code)
        
        # Should get rate limited eventually
        self.assertIn(429, responses)
    
    def test_failed_authentication_tracking(self):
        """Test failed authentication attempt tracking."""
        # Make multiple failed login attempts
        for i in range(6):
            response = self.client.post('/accounts/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # IP should be tracked for failed attempts
        from apps.core.rate_limiting import FailedAttemptTracker
        tracker = FailedAttemptTracker()
        attempts = tracker.get_failed_attempts('127.0.0.1', 'login')
        self.assertGreater(attempts, 0)
    
    def test_security_logging(self):
        """Test security event logging."""
        with self.assertLogs('security', level='WARNING') as log:
            # Trigger a security event
            response = self.client.get('/test/?q=<script>alert(1)</script>')
            
            # Should have logged security event
            self.assertTrue(any('suspicious' in message.lower() for message in log.output))


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_rate_limiting_csrf'])
    
    if failures:
        exit(1)