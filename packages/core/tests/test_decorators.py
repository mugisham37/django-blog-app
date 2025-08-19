"""
Unit tests for enterprise_core.decorators module.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.cache import cache

from enterprise_core.decorators import (
    require_authentication,
    require_permission,
    require_role,
    rate_limit,
    validate_content_security,
    _contains_xss,
    _contains_sql_injection,
)


class MockRequest:
    """Mock request object for testing."""
    
    def __init__(self, path='/', method='GET', user=None, post_data=None):
        self.path = path
        self.method = method
        self.user = user or Mock()
        self.POST = post_data or {}
        self.META = {'REMOTE_ADDR': '127.0.0.1'}


class MockUser:
    """Mock user object for testing."""
    
    def __init__(self, is_authenticated=True, is_staff=False, is_superuser=False, 
                 permissions=None, groups=None):
        self.is_authenticated = is_authenticated
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.id = 1
        self.username = 'testuser'
        self._permissions = permissions or []
        self._groups = groups or []
    
    def has_perm(self, permission):
        return permission in self._permissions
    
    def get_all_permissions(self):
        return self._permissions
    
    @property
    def groups(self):
        mock_groups = Mock()
        mock_groups.filter.return_value.exists.return_value = any(
            group in self._groups for group in self._groups
        )
        mock_groups.values_list.return_value = self._groups
        return mock_groups


class TestRequireAuthentication:
    """Test require_authentication decorator."""
    
    def test_authenticated_user_access(self):
        """Test that authenticated users can access decorated views."""
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(is_authenticated=True)
        request = MockRequest(user=user)
        
        response = test_view(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'success'
    
    def test_unauthenticated_user_api_response(self):
        """Test JSON response for API endpoints when unauthenticated."""
        @require_authentication(api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(is_authenticated=False)
        request = MockRequest(path='/api/test/', user=user)
        
        response = test_view(request)
        
        assert response.status_code == 401
        data = json.loads(response.content)
        assert data['error'] == 'UserNotAuthenticatedException'


class TestRequirePermission:
    """Test require_permission decorator."""
    
    def test_user_with_permission_access(self):
        """Test that users with required permission can access view."""
        @require_permission('auth.test_permission')
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(permissions=['auth.test_permission'])
        request = MockRequest(user=user)
        
        response = test_view(request)
        
        assert response.status_code == 200
    
    def test_user_without_permission_denied(self):
        """Test that users without required permission are denied."""
        @require_permission('auth.test_permission', api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(permissions=[])
        request = MockRequest(path='/api/test/', user=user)
        
        response = test_view(request)
        
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['error'] == 'InsufficientPermissionsException'


class TestRequireRole:
    """Test require_role decorator."""
    
    def test_user_with_role_access(self):
        """Test that users with required role can access view."""
        @require_role('editors')
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(groups=['editors'])
        # Mock the groups.filter().exists() call
        user.groups.filter.return_value.exists.return_value = True
        request = MockRequest(user=user)
        
        response = test_view(request)
        
        assert response.status_code == 200
    
    def test_user_without_role_denied(self):
        """Test that users without required role are denied."""
        @require_role('editors', api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser(groups=[])
        # Mock the groups.filter().exists() call
        user.groups.filter.return_value.exists.return_value = False
        request = MockRequest(path='/api/test/', user=user)
        
        response = test_view(request)
        
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['error'] == 'InsufficientPermissionsException'


class TestRateLimit:
    """Test rate_limit decorator."""
    
    def setUp(self):
        """Clear cache before each test."""
        cache.clear()
    
    def test_rate_limit_not_exceeded(self):
        """Test that requests within rate limit are allowed."""
        cache.clear()
        
        @rate_limit(requests_per_minute=5, per_user=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser()
        request = MockRequest(user=user)
        
        # Make 3 requests (within limit of 5)
        for i in range(3):
            response = test_view(request)
            assert response.status_code == 200
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding rate limit are blocked."""
        cache.clear()
        
        @rate_limit(requests_per_minute=2, per_user=True, api_response=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        user = MockUser()
        request = MockRequest(path='/api/test/', user=user)
        
        # Make requests up to the limit
        for i in range(2):
            response = test_view(request)
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = test_view(request)
        assert response.status_code == 429
        data = json.loads(response.content)
        assert data['error'] == 'RateLimitExceededException'


class TestValidateContentSecurity:
    """Test validate_content_security decorator."""
    
    def test_safe_content(self):
        """Test that safe content is allowed."""
        @validate_content_security()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = MockRequest(method='POST', post_data={'content': 'Safe content here'})
        
        response = test_view(request)
        
        assert response.status_code == 200
    
    def test_xss_content_blocked(self):
        """Test that XSS content is blocked."""
        @validate_content_security(check_xss=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = MockRequest(
            path='/api/test/', 
            method='POST', 
            post_data={'content': '<script>alert("xss")</script>'}
        )
        
        response = test_view(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error'] == 'XSSAttemptException'
    
    def test_sql_injection_blocked(self):
        """Test that SQL injection attempts are blocked."""
        @validate_content_security(check_sql_injection=True)
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = MockRequest(
            path='/api/test/', 
            method='POST', 
            post_data={'query': 'SELECT * FROM users WHERE 1=1'}
        )
        
        response = test_view(request)
        
        assert response.status_code == 400


class TestHelperFunctions:
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
            assert _contains_xss(sample), f"Should detect XSS in: {sample}"
        
        safe_samples = [
            'This is safe content',
            '<p>Safe HTML paragraph</p>',
            'Normal text with numbers 123',
        ]
        
        for sample in safe_samples:
            assert not _contains_xss(sample), f"Should not detect XSS in: {sample}"
    
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
            assert _contains_sql_injection(sample), f"Should detect SQL injection in: {sample}"
        
        safe_samples = [
            'This is safe content',
            'Search for python tutorials',
            'Normal query text',
        ]
        
        for sample in safe_samples:
            assert not _contains_sql_injection(sample), f"Should not detect SQL injection in: {sample}"