"""
Tests for core middleware in Django Personal Blog System.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.core.cache import cache

from apps.core.middleware import (
    ErrorHandlingMiddleware,
    SecurityMiddleware,
    AnalyticsMiddleware,
    RequestLoggingMiddleware
)
from apps.core.exceptions import (
    BlogException,
    PostNotFoundException,
    UserNotAuthenticatedException,
    InsufficientPermissionsException,
    RateLimitExceededException,
    SuspiciousOperationException,
    SecurityException
)

User = get_user_model()


class ErrorHandlingMiddlewareTestCase(TestCase):
    """Test ErrorHandlingMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = ErrorHandlingMiddleware(lambda request: None)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_blog_exception_handling_api(self):
        """Test handling of BlogException for API requests."""
        request = self.factory.get('/api/posts/123/')
        request.user = self.user
        
        exception = PostNotFoundException(post_id=123)
        
        response = self.middleware.process_exception(request, exception)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'PostNotFoundException')
        self.assertEqual(data['code'], 'POST_NOT_FOUND')
    
    def test_blog_exception_handling_web(self):
        """Test handling of BlogException for web requests."""
        request = self.factory.get('/posts/123/')
        request.user = self.user
        
        exception = PostNotFoundException(post_id=123)
        
        with patch('apps.core.middleware.render') as mock_render:
            mock_render.return_value = MagicMock(status_code=404)
            response = self.middleware.process_exception(request, exception)
            
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], request)
            self.assertEqual(args[1], 'errors/404.html')
            self.assertEqual(kwargs['status'], 404)
    
    def test_security_exception_logging(self):
        """Test that security exceptions are logged."""
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        exception = SuspiciousOperationException(
            operation="test_operation",
            ip_address="192.168.1.1"
        )
        
        with patch('apps.core.middleware.log_security_event') as mock_log:
            response = self.middleware.process_exception(request, exception)
            mock_log.assert_called_once_with(exception, request, self.user)
    
    def test_generic_exception_handling_api(self):
        """Test handling of generic exceptions for API requests."""
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        exception = ValueError("Generic error")
        
        response = self.middleware.process_exception(request, exception)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Internal server error')
        self.assertEqual(data['code'], 'INTERNAL_ERROR')
    
    def test_generic_exception_handling_web(self):
        """Test handling of generic exceptions for web requests."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        exception = ValueError("Generic error")
        
        with patch('apps.core.middleware.render') as mock_render:
            mock_render.return_value = MagicMock(status_code=500)
            response = self.middleware.process_exception(request, exception)
            
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[1], 'errors/500.html')
            self.assertEqual(kwargs['status'], 500)
    
    def test_status_code_mapping(self):
        """Test correct status code mapping for different exceptions."""
        test_cases = [
            (PostNotFoundException(), 404),
            (UserNotAuthenticatedException(), 401),
            (InsufficientPermissionsException(), 403),
            (RateLimitExceededException(), 429),
        ]
        
        for exception, expected_status in test_cases:
            with self.subTest(exception=exception.__class__.__name__):
                status = self.middleware._get_status_code(exception)
                self.assertEqual(status, expected_status)
    
    def test_template_mapping(self):
        """Test correct template mapping for different exceptions."""
        test_cases = [
            (PostNotFoundException(), 'errors/404.html'),
            (UserNotAuthenticatedException(), 'errors/401.html'),
            (InsufficientPermissionsException(), 'errors/403.html'),
            (RateLimitExceededException(), 'errors/429.html'),
        ]
        
        for exception, expected_template in test_cases:
            with self.subTest(exception=exception.__class__.__name__):
                template = self.middleware._get_error_template(exception)
                self.assertEqual(template, expected_template)


class SecurityMiddlewareTestCase(TestCase):
    """Test SecurityMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: JsonResponse({'status': 'ok'}))
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def test_skip_security_check_for_static_files(self):
        """Test that security checks are skipped for static files."""
        request = self.factory.get('/static/css/style.css')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)
    
    def test_suspicious_request_detection(self):
        """Test detection of suspicious request patterns."""
        suspicious_paths = [
            '/test/../../../etc/passwd',
            '/test?param=<script>alert(1)</script>',
            '/test?query=union select * from users',
        ]
        
        for path in suspicious_paths:
            with self.subTest(path=path):
                request = self.factory.get(path)
                request.user = self.user
                
                response = self.middleware.process_request(request)
                
                self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_suspicious_user_agent_detection(self):
        """Test detection of suspicious user agents."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'sqlmap/1.0'
        
        response = self.middleware.process_request(request)
        
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_anonymous_rate_limiting(self):
        """Test rate limiting for anonymous users."""
        request = self.factory.get('/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Set cache to simulate many requests
        cache.set('anon_rate_limit_192.168.1.1', 100, 60)
        
        response = self.middleware.process_request(request)
        
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = JsonResponse({'status': 'ok'})
        response = self.middleware.process_response(request, response)
        
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Content-Security-Policy'
        ]
        
        for header in expected_headers:
            with self.subTest(header=header):
                self.assertIn(header, response)
    
    def test_csp_header_not_added_for_admin(self):
        """Test that CSP header is not added for admin pages."""
        request = self.factory.get('/admin/users/')
        request.user = self.user
        
        response = JsonResponse({'status': 'ok'})
        response = self.middleware.process_response(request, response)
        
        self.assertNotIn('Content-Security-Policy', response)
    
    def test_normal_request_processing(self):
        """Test that normal requests are processed without issues."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Normal Browser)'
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)


class AnalyticsMiddlewareTestCase(TestCase):
    """Test AnalyticsMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = AnalyticsMiddleware(lambda request: JsonResponse({'status': 'ok'}))
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_skip_tracking_for_static_files(self):
        """Test that tracking is skipped for static files."""
        request = self.factory.get('/static/css/style.css')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)
        self.assertFalse(hasattr(request, '_analytics_start_time'))
    
    def test_request_timing_tracking(self):
        """Test that request timing is tracked."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Process request
        self.middleware.process_request(request)
        
        self.assertTrue(hasattr(request, '_analytics_start_time'))
        self.assertIsInstance(request._analytics_start_time, float)
    
    @patch('apps.core.middleware.logger')
    def test_slow_request_logging(self, mock_logger):
        """Test that slow requests are logged."""
        request = self.factory.get('/test/')
        request.user = self.user
        request._analytics_start_time = 0.0  # Very old timestamp to simulate slow request
        
        response = JsonResponse({'status': 'ok'})
        self.middleware.process_response(request, response)
        
        mock_logger.warning.assert_called_once()
        log_call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('Slow request', log_call_args)
    
    @patch('apps.core.middleware.logger')
    def test_page_view_tracking(self, mock_logger):
        """Test that page views are tracked."""
        request = self.factory.get('/posts/123/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        self.middleware.process_request(request)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Page view', log_call_args)
        self.assertIn('/posts/123/', log_call_args)
    
    def test_skip_tracking_paths(self):
        """Test that certain paths are skipped for tracking."""
        skip_paths = [
            '/static/css/style.css',
            '/media/images/photo.jpg',
            '/favicon.ico',
            '/robots.txt',
            '/health/',
        ]
        
        for path in skip_paths:
            with self.subTest(path=path):
                self.assertTrue(self.middleware._should_skip_tracking(
                    self.factory.get(path)
                ))


class RequestLoggingMiddlewareTestCase(TestCase):
    """Test RequestLoggingMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(lambda request: JsonResponse({'status': 'ok'}))
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_skip_logging_for_static_files(self):
        """Test that logging is skipped for static files."""
        request = self.factory.get('/static/css/style.css')
        request.user = self.user
        
        with patch('apps.core.middleware.logger') as mock_logger:
            self.middleware.process_request(request)
            mock_logger.info.assert_not_called()
    
    @patch('apps.core.middleware.logger')
    def test_request_logging_authenticated_user(self, mock_logger):
        """Test request logging for authenticated users."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        self.middleware.process_request(request)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Request:', log_call_args)
    
    @patch('apps.core.middleware.logger')
    def test_request_logging_anonymous_user(self, mock_logger):
        """Test request logging for anonymous users."""
        request = self.factory.get('/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        self.middleware.process_request(request)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Request:', log_call_args)
    
    @patch('apps.core.middleware.logger')
    def test_post_data_logging_with_sensitive_fields(self, mock_logger):
        """Test that sensitive fields in POST data are masked."""
        post_data = json.dumps({
            'username': 'testuser',
            'password': 'secret123',
            'email': 'test@example.com',
            'api_key': 'secret_key'
        })
        
        request = self.factory.post(
            '/test/',
            data=post_data,
            content_type='application/json'
        )
        request.user = self.user
        
        self.middleware.process_request(request)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        
        # Check that sensitive fields are masked
        self.assertIn('***', log_call_args)
        self.assertNotIn('secret123', log_call_args)
        self.assertNotIn('secret_key', log_call_args)
    
    def test_skip_logging_paths(self):
        """Test that certain paths are skipped for logging."""
        skip_paths = [
            '/static/css/style.css',
            '/media/images/photo.jpg',
            '/favicon.ico',
            '/health/',
        ]
        
        for path in skip_paths:
            with self.subTest(path=path):
                self.assertTrue(self.middleware._should_skip_logging(
                    self.factory.get(path)
                ))


class MiddlewareIntegrationTestCase(TestCase):
    """Test middleware integration and interaction."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_middleware_chain_processing(self):
        """Test that multiple middleware can work together."""
        # Create a chain of middleware
        def get_response(request):
            return JsonResponse({'status': 'success'})
        
        error_middleware = ErrorHandlingMiddleware(get_response)
        security_middleware = SecurityMiddleware(error_middleware)
        analytics_middleware = AnalyticsMiddleware(security_middleware)
        logging_middleware = RequestLoggingMiddleware(analytics_middleware)
        
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        # Process request through middleware chain
        with patch('apps.core.middleware.logger'):
            response = logging_middleware(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
    
    def test_middleware_exception_handling_in_chain(self):
        """Test exception handling in middleware chain."""
        def get_response(request):
            raise PostNotFoundException(post_id=123)
        
        error_middleware = ErrorHandlingMiddleware(get_response)
        security_middleware = SecurityMiddleware(error_middleware)
        
        request = self.factory.get('/api/posts/123/')
        request.user = self.user
        
        response = security_middleware(request)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'PostNotFoundException')