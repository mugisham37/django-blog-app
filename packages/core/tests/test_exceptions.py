"""
Unit tests for enterprise_core.exceptions module.
"""

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from enterprise_core.exceptions import (
    BusinessLogicError,
    ValidationError,
    AuthenticationError,
    ContentError,
    PostNotFoundException,
    UserNotAuthenticatedException,
    RateLimitExceededException,
    handle_django_validation_error,
    get_client_ip,
)


class TestBusinessLogicError:
    """Test BusinessLogicError base exception."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exception = BusinessLogicError("Test error")
        
        assert str(exception) == "Test error"
        assert exception.message == "Test error"
        assert exception.code == "BusinessLogicError"
        assert exception.details == {}
    
    def test_exception_with_code_and_details(self):
        """Test exception with code and details."""
        details = {'field': 'value', 'error_count': 2}
        exception = BusinessLogicError("Test error", code="TEST_ERROR", details=details)
        
        assert exception.code == "TEST_ERROR"
        assert exception.details == details
    
    def test_to_dict_method(self):
        """Test exception to_dict method."""
        exception = BusinessLogicError("Test error", code="TEST_ERROR", details={'key': 'value'})
        expected_dict = {
            'error': 'BusinessLogicError',
            'message': 'Test error',
            'code': 'TEST_ERROR',
            'details': {'key': 'value'}
        }
        
        assert exception.to_dict() == expected_dict


class TestSpecificExceptions:
    """Test specific exception classes."""
    
    def test_post_not_found_exception(self):
        """Test PostNotFoundException."""
        # With post ID
        exception = PostNotFoundException(post_id=123)
        assert "123" in str(exception)
        assert exception.code == "POST_NOT_FOUND"
        assert exception.details['post_id'] == 123
        
        # With slug
        exception = PostNotFoundException(slug="test-post")
        assert "test-post" in str(exception)
        assert exception.details['slug'] == "test-post"
    
    def test_user_not_authenticated_exception(self):
        """Test UserNotAuthenticatedException."""
        exception = UserNotAuthenticatedException(required_action="view post")
        
        assert "Authentication required" in str(exception)
        assert "view post" in str(exception)
        assert exception.code == "AUTHENTICATION_REQUIRED"
        assert exception.details['required_action'] == "view post"
    
    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceededException."""
        exception = RateLimitExceededException(
            limit_type="API requests",
            retry_after=60
        )
        
        assert "Rate limit exceeded" in str(exception)
        assert "API requests" in str(exception)
        assert "60 seconds" in str(exception)
        assert exception.code == "RATE_LIMIT_EXCEEDED"
        assert exception.details['limit_type'] == "API requests"
        assert exception.details['retry_after'] == 60


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_handle_django_validation_error_with_error_dict(self):
        """Test handling Django ValidationError with error_dict."""
        validation_error = DjangoValidationError({
            'title': ['This field is required.'],
            'content': ['Content is too short.', 'Invalid format.']
        })
        
        blog_exception = handle_django_validation_error(validation_error)
        
        assert len(blog_exception.details['errors']) == 3
        assert 'This field is required.' in blog_exception.details['errors']
        assert 'Content is too short.' in blog_exception.details['errors']
        assert 'Invalid format.' in blog_exception.details['errors']
    
    def test_handle_django_validation_error_single_message(self):
        """Test handling Django ValidationError with single message."""
        validation_error = DjangoValidationError('Single error message')
        
        blog_exception = handle_django_validation_error(validation_error)
        
        assert len(blog_exception.details['errors']) == 1
        assert 'Single error message' in blog_exception.details['errors']
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test getting client IP with X-Forwarded-For header."""
        class MockRequest:
            META = {
                'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1',
                'REMOTE_ADDR': '127.0.0.1'
            }
        
        request = MockRequest()
        ip = get_client_ip(request)
        
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test getting client IP without X-Forwarded-For header."""
        class MockRequest:
            META = {'REMOTE_ADDR': '192.168.1.100'}
        
        request = MockRequest()
        ip = get_client_ip(request)
        
        assert ip == '192.168.1.100'


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from appropriate base classes."""
        # Content exceptions
        assert isinstance(PostNotFoundException(), ContentError)
        assert isinstance(PostNotFoundException(), BusinessLogicError)
        
        # Authentication exceptions
        assert isinstance(UserNotAuthenticatedException(), AuthenticationError)
        assert isinstance(UserNotAuthenticatedException(), BusinessLogicError)
        
        # Rate limit exceptions
        assert isinstance(RateLimitExceededException(), BusinessLogicError)