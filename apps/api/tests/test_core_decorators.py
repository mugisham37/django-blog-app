"""
Tests for core decorators in Django Personal Blog System.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseForbidden
from django.core.cache import cache
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.core.decorators import (
    require_authentication,
    require_permission,
    require_role,
    require_staff,
    require_superuser,
    require_ownership,
    rate_limit,
    log_access,
    detect_suspicious_activity,
    validate_content_security,
    AuthenticationRequiredMixin,
    PermissionRequiredMixin,
    StaffRequiredMixin,
    SuperuserRequiredMixin,
    RateLimitMixin,
    _contains_xss,
    _contains_sql_injection
)

User = get_user_model()


class RequireAuthenticationTestCase(TestCase):
    """Test require_authentication decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_authenticated_user_access(self):
        """Test that authenticated users can access decorated views."""
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
    
    def test_unauthenticated_user_redirect(self):
        """Test that unauthenticated users are redirected."""
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        with patch('apps.core.decorators.reverse') as mock_reverse:
            mock_reverse.return_value = '/login/'
            response = test_view(request)
        
        self.assertEqual(response.status_code, 302)
    
    def test_api_response_for_unauthenticated(self):
        """Test JSON response for API endpoints when unauthenticated."""
        @require_authentication(api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'UserNotAuthenticatedException')


class RequirePermissionTestCase(TestCase):
    """Test require_permission decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test permission
        content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type
        )
    
    def test_user_with_permission_access(self):
        """Test that users with required permission can access view."""
        self.user.user_permissions.add(self.permission)
        
        @require_permission('auth.test_permission')
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_user_without_permission_denied(self):
        """Test that users without required permission are denied."""
        @require_permission('auth.test_permission', api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'InsufficientPermissionsException')


class RequireRoleTestCase(TestCase):
    """Test require_role decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = Group.objects.create(name='editors')
    
    def test_user_with_role_access(self):
        """Test that users with required role can access view."""
        self.user.groups.add(self.group)
        
        @require_role('editors')
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_user_without_role_denied(self):
        """Test that users without required role are denied."""
        @require_role('editors', api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'InsufficientPermissionsException')


class RequireStaffTestCase(TestCase):
    """Test require_staff decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
    
    def test_staff_user_access(self):
        """Test that staff users can access decorated views."""
        @require_staff()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.staff_user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_denied(self):
        """Test that regular users are denied access."""
        @require_staff(api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.regular_user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)


class RequireSuperuserTestCase(TestCase):
    """Test require_superuser decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@example.com',
            password='testpass123',
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
    
    def test_superuser_access(self):
        """Test that superusers can access decorated views."""
        @require_superuser()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.superuser
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_denied(self):
        """Test that regular users are denied access."""
        @require_superuser(api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.regular_user
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)


class RequireOwnershipTestCase(TestCase):
    """Test require_ownership decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create a mock model instance
        self.mock_object = MagicMock()
        self.mock_object.author = self.owner
    
    @patch('apps.core.decorators.User')  # Mock the model class
    def test_owner_access(self, mock_model):
        """Test that object owners can access decorated views."""
        mock_model.objects.get.return_value = self.mock_object
        
        @require_ownership(mock_model, lookup_field='pk')
        def test_view(request, pk):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.owner
        
        response = test_view(request, pk=1)
        
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.core.decorators.User')  # Mock the model class
    def test_non_owner_denied(self, mock_model):
        """Test that non-owners are denied access."""
        mock_model.objects.get.return_value = self.mock_object
        
        @require_ownership(mock_model, lookup_field='pk', api_response=True)
        def test_view(request, pk):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.other_user
        
        response = test_view(request, pk=1)
        
        self.assertEqual(response.status_code, 403)


class RateLimitTestCase(TestCase):
    """Test rate_limit decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Clear cache before each test
        cache.clear()
    
    def test_rate_limit_not_exceeded(self):
        """Test that requests within rate limit are allowed."""
        @rate_limit(requests_per_minute=5, per_user=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Make 3 requests (within limit of 5)
        for i in range(3):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding rate limit are blocked."""
        @rate_limit(requests_per_minute=2, per_user=True, api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        # Make requests up to the limit
        for i in range(2):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'RateLimitExceededException')
    
    def test_rate_limit_per_ip(self):
        """Test rate limiting per IP address."""
        @rate_limit(requests_per_minute=2, per_user=False, api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/api/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Make requests up to the limit
        for i in range(2):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = test_view(request)
        self.assertEqual(response.status_code, 429)


class LogAccessTestCase(TestCase):
    """Test log_access decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.core.decorators.security_logger')
    def test_access_logging(self, mock_logger):
        """Test that access is logged properly."""
        @log_access("test_action")
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
        mock_logger.info.assert_called_once()
        
        # Check that log contains expected information
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn('test_action', log_call_args)


class DetectSuspiciousActivityTestCase(TestCase):
    """Test detect_suspicious_activity decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        cache.clear()
    
    def test_normal_activity(self):
        """Test that normal activity is allowed."""
        @detect_suspicious_activity(max_failed_attempts=3)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_suspicious_activity_lockout(self):
        """Test that suspicious activity triggers lockout."""
        @detect_suspicious_activity(max_failed_attempts=2, lockout_duration=60)
        def test_view(request):
            # Simulate failed authentication
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Make failed attempts up to the limit
        for i in range(2):
            response = test_view(request)
            self.assertEqual(response.status_code, 401)
        
        # Next request should be blocked
        response = test_view(request)
        self.assertEqual(response.status_code, 403)


class ValidateContentSecurityTestCase(TestCase):
    """Test validate_content_security decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
    
    def test_safe_content(self):
        """Test that safe content is allowed."""
        @validate_content_security()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/test/', {'content': 'Safe content here'})
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_xss_content_blocked(self):
        """Test that XSS content is blocked."""
        @validate_content_security(check_xss=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/api/test/', {'content': '<script>alert("xss")</script>'})
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'XSSAttemptException')
    
    def test_sql_injection_blocked(self):
        """Test that SQL injection attempts are blocked."""
        @validate_content_security(check_sql_injection=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/api/test/', {'query': 'SELECT * FROM users WHERE 1=1'})
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 400)


class MixinTestCase(TestCase):
    """Test class-based view mixins."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_authentication_required_mixin(self):
        """Test AuthenticationRequiredMixin."""
        from django.views.generic import View
        
        class TestView(AuthenticationRequiredMixin, View):
            def get(self, request):
                return JsonResponse({'status': 'success'})
        
        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_staff_required_mixin(self):
        """Test StaffRequiredMixin."""
        from django.views.generic import View
        
        class TestView(StaffRequiredMixin, View):
            def get(self, request):
                return JsonResponse({'status': 'success'})
        
        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_mixin(self):
        """Test RateLimitMixin."""
        from django.views.generic import View
        
        class TestView(RateLimitMixin, View):
            rate_limit_requests = 2
            
            def get(self, request):
                return JsonResponse({'status': 'success'})
        
        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Clear cache
        cache.clear()
        
        # Make requests within limit
        for i in range(2):
            response = view(request)
            self.assertEqual(response.status_code, 200)


class HelperFunctionTestCase(TestCase):
    """Test helper functions."""
    
    def test_contains_xss(self):
        """Test XSS detection function."""
        xss_samples = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            '<img src="x" onerror="alert(1)">',
            'onclick="malicious()"',
            'document.cookie',
        ]
        
        for sample in xss_samples:
            with self.subTest(sample=sample):
                self.assertTrue(_contains_xss(sample))
        
        safe_samples = [
            'This is safe content',
            '<p>Safe HTML paragraph</p>',
            'Normal text with numbers 123',
        ]
        
        for sample in safe_samples:
            with self.subTest(sample=sample):
                self.assertFalse(_contains_xss(sample))
    
    def test_contains_sql_injection(self):
        """Test SQL injection detection function."""
        sql_samples = [
            'SELECT * FROM users WHERE 1=1',
            'DROP TABLE posts',
            'UNION SELECT password FROM users',
            'exec(malicious_code)',
            'OR 1=1--',
        ]
        
        for sample in sql_samples:
            with self.subTest(sample=sample):
                self.assertTrue(_contains_sql_injection(sample))
        
        safe_samples = [
            'This is safe content',
            'Search for python tutorials',
            'Normal query text',
        ]
        
        for sample in safe_samples:
            with self.subTest(sample=sample):
                self.assertFalse(_contains_sql_injection(sample))