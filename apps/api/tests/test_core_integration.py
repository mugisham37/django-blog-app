"""
Integration tests for core components in Django Personal Blog System.
Tests the interaction between validators, exceptions, decorators, and middleware.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.core.cache import cache

from apps.core.validators import validate_html_content, validate_password_strength
from apps.core.exceptions import (
    ContentValidationException, 
    XSSAttemptException,
    handle_django_validation_error
)
from apps.core.decorators import (
    require_authentication, 
    validate_content_security,
    rate_limit
)
from apps.core.middleware import (
    ErrorHandlingMiddleware,
    SecurityMiddleware
)

User = get_user_model()


class CoreIntegrationTestCase(TestCase):
    """Test integration between core components."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        cache.clear()
    
    def test_validator_exception_middleware_integration(self):
        """Test that validator exceptions are properly handled by middleware."""
        # Create a view that uses validators
        @require_authentication()
        def test_view(request):
            try:
                # This should raise a ValidationError
                validate_html_content('<script>alert("xss")</script>')
                return JsonResponse({'status': 'success'})
            except ValidationError as e:
                # Convert to BlogException
                blog_exception = handle_django_validation_error(e)
                raise blog_exception
        
        # Set up middleware
        middleware = ErrorHandlingMiddleware(test_view)
        
        # Create request
        request = self.factory.post('/api/test/')
        request.user = self.user
        
        # Process request through middleware
        response = middleware(request)
        
        # Should return proper error response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'ContentValidationException')
    
    def test_decorator_security_middleware_integration(self):
        """Test that decorators work with security middleware."""
        @validate_content_security(check_xss=True)
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        # Set up middleware chain
        error_middleware = ErrorHandlingMiddleware(test_view)
        security_middleware = SecurityMiddleware(error_middleware)
        
        # Create malicious request
        request = self.factory.post('/api/test/', {
            'content': '<script>alert("xss")</script>'
        })
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'Normal Browser'
        
        # Process request
        response = security_middleware(request)
        
        # Should be blocked by content security decorator
        self.assertEqual(response.status_code, 400)
    
    def test_rate_limiting_with_middleware(self):
        """Test rate limiting decorator with middleware."""
        @rate_limit(requests_per_minute=2, per_user=True, api_response=True)
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        # Set up middleware
        middleware = ErrorHandlingMiddleware(test_view)
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        # Make requests up to limit
        for i in range(2):
            response = middleware(request)
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = middleware(request)
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'RateLimitExceededException')
    
    def test_suspicious_activity_detection_chain(self):
        """Test suspicious activity detection across components."""
        # Create view with multiple security layers
        @validate_content_security(check_xss=True, check_sql_injection=True)
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        # Set up middleware
        security_middleware = SecurityMiddleware(test_view)
        
        # Create suspicious request
        request = self.factory.post('/api/test/', {
            'query': 'SELECT * FROM users WHERE 1=1'
        })
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'sqlmap/1.0'  # Suspicious user agent
        
        # Process request
        response = security_middleware(request)
        
        # Should be blocked by security middleware due to suspicious user agent
        self.assertEqual(response.status_code, 403)
    
    def test_password_validation_integration(self):
        """Test password validation with exception handling."""
        weak_passwords = [
            'weak',
            'password123',
            'ALLUPPERCASE',
            'nouppercase123!',
        ]
        
        for password in weak_passwords:
            with self.subTest(password=password):
                try:
                    validate_password_strength(password)
                    self.fail(f"Weak password '{password}' should have raised ValidationError")
                except ValidationError as e:
                    # Convert to BlogException
                    blog_exception = handle_django_validation_error(e)
                    self.assertIsInstance(blog_exception, ContentValidationException)
                    self.assertTrue(len(blog_exception.details['errors']) > 0)
    
    @override_settings(BLACKLISTED_EMAIL_DOMAINS=['spam.com'])
    def test_email_validation_with_settings(self):
        """Test email validation using Django settings."""
        from apps.core.validators import validate_email_domain
        
        # Valid email should pass
        try:
            validate_email_domain('user@example.com')
        except ValidationError:
            self.fail("Valid email should not raise ValidationError")
        
        # Blacklisted domain should fail
        with self.assertRaises(ValidationError):
            validate_email_domain('user@spam.com')
    
    def test_file_upload_validation_chain(self):
        """Test file upload validation with security checks."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.core.validators import validate_file_upload
        
        # Create malicious file
        malicious_file = SimpleUploadedFile(
            name='malicious.exe',
            content=b'Malicious executable content',
            content_type='application/octet-stream'
        )
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            validate_file_upload(malicious_file)
        
        # Convert to BlogException
        blog_exception = handle_django_validation_error(context.exception)
        self.assertIsInstance(blog_exception, ContentValidationException)
        self.assertIn('not allowed', str(blog_exception))
    
    def test_middleware_order_and_interaction(self):
        """Test that middleware components work in the correct order."""
        def get_response(request):
            return JsonResponse({'status': 'success'})
        
        # Create middleware chain in correct order
        error_middleware = ErrorHandlingMiddleware(get_response)
        security_middleware = SecurityMiddleware(error_middleware)
        
        # Normal request should pass through
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'Normal Browser'
        
        response = security_middleware(request)
        
        self.assertEqual(response.status_code, 200)
        # Should have security headers added
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
    
    def test_exception_logging_integration(self):
        """Test that exceptions are properly logged through the system."""
        from apps.core.exceptions import log_security_event, XSSAttemptException
        
        request = self.factory.post('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        exception = XSSAttemptException(
            content='<script>alert("test")</script>',
            field='comment'
        )
        
        # This should not raise any exceptions
        try:
            log_security_event(exception, request, self.user)
        except Exception as e:
            self.fail(f"Security event logging failed: {e}")
    
    def test_comprehensive_security_validation(self):
        """Test comprehensive security validation across all components."""
        # Test various attack vectors
        attack_vectors = [
            {
                'name': 'XSS in POST data',
                'data': {'content': '<script>alert("xss")</script>'},
                'expected_blocked': True
            },
            {
                'name': 'SQL injection in POST data',
                'data': {'query': 'DROP TABLE users'},
                'expected_blocked': True
            },
            {
                'name': 'Safe content',
                'data': {'content': 'This is safe content'},
                'expected_blocked': False
            }
        ]
        
        @validate_content_security(check_xss=True, check_sql_injection=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        for vector in attack_vectors:
            with self.subTest(attack=vector['name']):
                request = self.factory.post('/api/test/', vector['data'])
                request.user = self.user
                
                response = test_view(request)
                
                if vector['expected_blocked']:
                    self.assertEqual(response.status_code, 400)
                else:
                    self.assertEqual(response.status_code, 200)


class CoreComponentCompatibilityTestCase(TestCase):
    """Test compatibility between different core components."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_exception_serialization_for_api(self):
        """Test that exceptions can be properly serialized for API responses."""
        from apps.core.exceptions import (
            PostNotFoundException,
            InsufficientPermissionsException,
            RateLimitExceededException
        )
        
        exceptions = [
            PostNotFoundException(post_id=123),
            InsufficientPermissionsException(
                required_permission='blog.delete_post',
                user_permissions=['blog.view_post']
            ),
            RateLimitExceededException(limit_type='API', retry_after=60)
        ]
        
        for exception in exceptions:
            with self.subTest(exception=exception.__class__.__name__):
                # Should be able to convert to dict without errors
                exception_dict = exception.to_dict()
                
                # Should contain required fields
                self.assertIn('error', exception_dict)
                self.assertIn('message', exception_dict)
                self.assertIn('code', exception_dict)
                self.assertIn('details', exception_dict)
                
                # Should be JSON serializable
                try:
                    json.dumps(exception_dict)
                except (TypeError, ValueError) as e:
                    self.fail(f"Exception dict not JSON serializable: {e}")
    
    def test_validator_decorator_compatibility(self):
        """Test that validators work properly with decorators."""
        from apps.core.validators import validate_comment_content
        
        @require_authentication()
        def comment_view(request):
            if request.method == 'POST':
                content = request.POST.get('content', '')
                try:
                    validate_comment_content(content)
                    return JsonResponse({'status': 'success'})
                except ValidationError as e:
                    blog_exception = handle_django_validation_error(e)
                    raise blog_exception
            return JsonResponse({'status': 'ok'})
        
        # Test with valid content
        request = self.factory.post('/comment/', {'content': 'This is a valid comment.'})
        request.user = self.user
        
        response = comment_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with invalid content
        request = self.factory.post('/comment/', {'content': 'Hi'})  # Too short
        request.user = self.user
        
        with self.assertRaises(ContentValidationException):
            comment_view(request)
    
    def test_middleware_exception_propagation(self):
        """Test that exceptions propagate correctly through middleware."""
        from apps.core.exceptions import PostNotFoundException
        
        def view_that_raises(request):
            raise PostNotFoundException(post_id=123)
        
        middleware = ErrorHandlingMiddleware(view_that_raises)
        
        request = self.factory.get('/api/posts/123/')
        request.user = self.user
        
        response = middleware(request)
        
        # Should handle the exception and return appropriate response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'PostNotFoundException')
        self.assertEqual(data['code'], 'POST_NOT_FOUND')