"""
Tests for core exceptions in Django Personal Blog System.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.exceptions import (
    BlogException,
    ContentException,
    PostNotFoundException,
    PostNotPublishedException,
    CategoryNotFoundException,
    TagNotFoundException,
    ContentValidationException,
    DuplicateSlugException,
    AuthenticationException,
    UserNotAuthenticatedException,
    InsufficientPermissionsException,
    InvalidTokenException,
    AccountLockedException,
    CommentException,
    CommentNotFoundException,
    CommentModerationException,
    SpamDetectedException,
    RateLimitException,
    RateLimitExceededException,
    APIException,
    InvalidAPIRequestException,
    APIVersionNotSupportedException,
    FileUploadException,
    InvalidFileTypeException,
    FileSizeExceededException,
    SecurityException,
    SuspiciousOperationException,
    CSRFException,
    XSSAttemptException,
    handle_django_validation_error,
    log_security_event,
    get_client_ip
)

User = get_user_model()


class BlogExceptionTestCase(TestCase):
    """Test base BlogException class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exception = BlogException("Test error")
        
        self.assertEqual(str(exception), "Test error")
        self.assertEqual(exception.message, "Test error")
        self.assertIsNone(exception.code)
        self.assertEqual(exception.details, {})
    
    def test_exception_with_code_and_details(self):
        """Test exception with code and details."""
        details = {'field': 'value', 'error_count': 2}
        exception = BlogException("Test error", code="TEST_ERROR", details=details)
        
        self.assertEqual(exception.code, "TEST_ERROR")
        self.assertEqual(exception.details, details)
    
    def test_to_dict_method(self):
        """Test exception to_dict method."""
        exception = BlogException("Test error", code="TEST_ERROR", details={'key': 'value'})
        expected_dict = {
            'error': 'BlogException',
            'message': 'Test error',
            'code': 'TEST_ERROR',
            'details': {'key': 'value'}
        }
        
        self.assertEqual(exception.to_dict(), expected_dict)


class ContentExceptionTestCase(TestCase):
    """Test content-related exceptions."""
    
    def test_post_not_found_exception(self):
        """Test PostNotFoundException."""
        # With post ID
        exception = PostNotFoundException(post_id=123)
        self.assertIn("123", str(exception))
        self.assertEqual(exception.code, "POST_NOT_FOUND")
        self.assertEqual(exception.details['post_id'], 123)
        
        # With slug
        exception = PostNotFoundException(slug="test-post")
        self.assertIn("test-post", str(exception))
        self.assertEqual(exception.details['slug'], "test-post")
        
        # Without parameters
        exception = PostNotFoundException()
        self.assertIn("not found", str(exception).lower())
    
    def test_post_not_published_exception(self):
        """Test PostNotPublishedException."""
        exception = PostNotPublishedException(post_id=123, status="draft")
        
        self.assertIn("not published", str(exception).lower())
        self.assertEqual(exception.code, "POST_NOT_PUBLISHED")
        self.assertEqual(exception.details['post_id'], 123)
        self.assertEqual(exception.details['status'], "draft")
    
    def test_category_not_found_exception(self):
        """Test CategoryNotFoundException."""
        exception = CategoryNotFoundException(category_id=456)
        
        self.assertIn("456", str(exception))
        self.assertEqual(exception.code, "CATEGORY_NOT_FOUND")
        self.assertEqual(exception.details['category_id'], 456)
    
    def test_tag_not_found_exception(self):
        """Test TagNotFoundException."""
        exception = TagNotFoundException(slug="python")
        
        self.assertIn("python", str(exception))
        self.assertEqual(exception.code, "TAG_NOT_FOUND")
        self.assertEqual(exception.details['slug'], "python")
    
    def test_content_validation_exception(self):
        """Test ContentValidationException."""
        errors = ["Field is required", "Invalid format"]
        exception = ContentValidationException(field="title", errors=errors)
        
        self.assertIn("title", str(exception))
        self.assertEqual(exception.code, "CONTENT_VALIDATION_ERROR")
        self.assertEqual(exception.details['field'], "title")
        self.assertEqual(exception.details['errors'], errors)
    
    def test_duplicate_slug_exception(self):
        """Test DuplicateSlugException."""
        exception = DuplicateSlugException("test-slug", model_name="Post")
        
        self.assertIn("test-slug", str(exception))
        self.assertIn("Post", str(exception))
        self.assertEqual(exception.code, "DUPLICATE_SLUG")
        self.assertEqual(exception.details['slug'], "test-slug")
        self.assertEqual(exception.details['model'], "Post")


class AuthenticationExceptionTestCase(TestCase):
    """Test authentication-related exceptions."""
    
    def test_user_not_authenticated_exception(self):
        """Test UserNotAuthenticatedException."""
        exception = UserNotAuthenticatedException(required_action="view post")
        
        self.assertIn("Authentication required", str(exception))
        self.assertIn("view post", str(exception))
        self.assertEqual(exception.code, "AUTHENTICATION_REQUIRED")
        self.assertEqual(exception.details['required_action'], "view post")
    
    def test_insufficient_permissions_exception(self):
        """Test InsufficientPermissionsException."""
        user_perms = ["blog.view_post", "blog.add_comment"]
        exception = InsufficientPermissionsException(
            required_permission="blog.delete_post",
            user_permissions=user_perms
        )
        
        self.assertIn("Insufficient permissions", str(exception))
        self.assertIn("blog.delete_post", str(exception))
        self.assertEqual(exception.code, "INSUFFICIENT_PERMISSIONS")
        self.assertEqual(exception.details['required_permission'], "blog.delete_post")
        self.assertEqual(exception.details['user_permissions'], user_perms)
    
    def test_invalid_token_exception(self):
        """Test InvalidTokenException."""
        exception = InvalidTokenException(token_type="JWT")
        
        self.assertIn("invalid or expired", str(exception).lower())
        self.assertIn("JWT", str(exception))
        self.assertEqual(exception.code, "INVALID_TOKEN")
        self.assertEqual(exception.details['token_type'], "JWT")
    
    def test_account_locked_exception(self):
        """Test AccountLockedException."""
        exception = AccountLockedException(
            username="testuser",
            lock_reason="Too many failed attempts"
        )
        
        self.assertIn("locked", str(exception).lower())
        self.assertIn("Too many failed attempts", str(exception))
        self.assertEqual(exception.code, "ACCOUNT_LOCKED")
        self.assertEqual(exception.details['username'], "testuser")
        self.assertEqual(exception.details['lock_reason'], "Too many failed attempts")


class CommentExceptionTestCase(TestCase):
    """Test comment-related exceptions."""
    
    def test_comment_not_found_exception(self):
        """Test CommentNotFoundException."""
        exception = CommentNotFoundException(comment_id=789)
        
        self.assertIn("789", str(exception))
        self.assertEqual(exception.code, "COMMENT_NOT_FOUND")
        self.assertEqual(exception.details['comment_id'], 789)
    
    def test_comment_moderation_exception(self):
        """Test CommentModerationException."""
        exception = CommentModerationException(
            comment_id=123,
            reason="Contains spam"
        )
        
        self.assertIn("moderation failed", str(exception).lower())
        self.assertIn("Contains spam", str(exception))
        self.assertEqual(exception.code, "COMMENT_MODERATION_FAILED")
        self.assertEqual(exception.details['comment_id'], 123)
        self.assertEqual(exception.details['reason'], "Contains spam")
    
    def test_spam_detected_exception(self):
        """Test SpamDetectedException."""
        exception = SpamDetectedException(content_type="comment", spam_score=0.95)
        
        self.assertIn("Spam detected", str(exception))
        self.assertIn("comment", str(exception))
        self.assertEqual(exception.code, "SPAM_DETECTED")
        self.assertEqual(exception.details['content_type'], "comment")
        self.assertEqual(exception.details['spam_score'], 0.95)


class RateLimitExceptionTestCase(TestCase):
    """Test rate limiting exceptions."""
    
    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceededException."""
        exception = RateLimitExceededException(
            limit_type="API requests",
            retry_after=60
        )
        
        self.assertIn("Rate limit exceeded", str(exception))
        self.assertIn("API requests", str(exception))
        self.assertIn("60 seconds", str(exception))
        self.assertEqual(exception.code, "RATE_LIMIT_EXCEEDED")
        self.assertEqual(exception.details['limit_type'], "API requests")
        self.assertEqual(exception.details['retry_after'], 60)


class APIExceptionTestCase(TestCase):
    """Test API-related exceptions."""
    
    def test_invalid_api_request_exception(self):
        """Test InvalidAPIRequestException."""
        errors = ["Missing required field", "Invalid format"]
        exception = InvalidAPIRequestException(field="email", errors=errors)
        
        self.assertIn("Invalid API request", str(exception))
        self.assertIn("email", str(exception))
        self.assertEqual(exception.code, "INVALID_API_REQUEST")
        self.assertEqual(exception.details['field'], "email")
        self.assertEqual(exception.details['errors'], errors)
    
    def test_api_version_not_supported_exception(self):
        """Test APIVersionNotSupportedException."""
        supported_versions = ["v1", "v2"]
        exception = APIVersionNotSupportedException(
            requested_version="v3",
            supported_versions=supported_versions
        )
        
        self.assertIn("not supported", str(exception))
        self.assertIn("v3", str(exception))
        self.assertIn("v1, v2", str(exception))
        self.assertEqual(exception.code, "API_VERSION_NOT_SUPPORTED")
        self.assertEqual(exception.details['requested_version'], "v3")
        self.assertEqual(exception.details['supported_versions'], supported_versions)


class FileUploadExceptionTestCase(TestCase):
    """Test file upload exceptions."""
    
    def test_invalid_file_type_exception(self):
        """Test InvalidFileTypeException."""
        allowed_types = [".jpg", ".png", ".gif"]
        exception = InvalidFileTypeException(
            file_type=".exe",
            allowed_types=allowed_types
        )
        
        self.assertIn("not allowed", str(exception))
        self.assertIn(".exe", str(exception))
        self.assertIn(".jpg, .png, .gif", str(exception))
        self.assertEqual(exception.code, "INVALID_FILE_TYPE")
        self.assertEqual(exception.details['file_type'], ".exe")
        self.assertEqual(exception.details['allowed_types'], allowed_types)
    
    def test_file_size_exceeded_exception(self):
        """Test FileSizeExceededException."""
        exception = FileSizeExceededException(file_size=10, max_size=5)
        
        self.assertIn("exceeds maximum", str(exception))
        self.assertIn("10MB", str(exception))
        self.assertIn("5MB", str(exception))
        self.assertEqual(exception.code, "FILE_SIZE_EXCEEDED")
        self.assertEqual(exception.details['file_size'], 10)
        self.assertEqual(exception.details['max_size'], 5)


class SecurityExceptionTestCase(TestCase):
    """Test security-related exceptions."""
    
    def test_suspicious_operation_exception(self):
        """Test SuspiciousOperationException."""
        exception = SuspiciousOperationException(
            operation="SQL injection attempt",
            user_id=123,
            ip_address="192.168.1.1"
        )
        
        self.assertIn("Suspicious operation", str(exception))
        self.assertIn("SQL injection attempt", str(exception))
        self.assertEqual(exception.code, "SUSPICIOUS_OPERATION")
        self.assertEqual(exception.details['operation'], "SQL injection attempt")
        self.assertEqual(exception.details['user_id'], 123)
        self.assertEqual(exception.details['ip_address'], "192.168.1.1")
    
    def test_csrf_exception(self):
        """Test CSRFException."""
        exception = CSRFException(request_path="/api/posts/")
        
        self.assertIn("CSRF validation failed", str(exception))
        self.assertIn("/api/posts/", str(exception))
        self.assertEqual(exception.code, "CSRF_FAILED")
        self.assertEqual(exception.details['request_path'], "/api/posts/")
    
    def test_xss_attempt_exception(self):
        """Test XSSAttemptException."""
        malicious_content = "<script>alert('xss')</script>"
        exception = XSSAttemptException(content=malicious_content, field="comment")
        
        self.assertIn("XSS attempt detected", str(exception))
        self.assertIn("comment", str(exception))
        self.assertEqual(exception.code, "XSS_ATTEMPT")
        self.assertEqual(exception.details['field'], "comment")
        # Content should be truncated to 100 characters
        self.assertEqual(len(exception.details['content']), len(malicious_content))


class UtilityFunctionTestCase(TestCase):
    """Test utility functions for exception handling."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_handle_django_validation_error_with_error_dict(self):
        """Test handling Django ValidationError with error_dict."""
        validation_error = ValidationError({
            'title': ['This field is required.'],
            'content': ['Content is too short.', 'Invalid format.']
        })
        
        blog_exception = handle_django_validation_error(validation_error)
        
        self.assertIsInstance(blog_exception, ContentValidationException)
        self.assertEqual(len(blog_exception.details['errors']), 3)
        self.assertIn('This field is required.', blog_exception.details['errors'])
        self.assertIn('Content is too short.', blog_exception.details['errors'])
        self.assertIn('Invalid format.', blog_exception.details['errors'])
    
    def test_handle_django_validation_error_with_error_list(self):
        """Test handling Django ValidationError with error_list."""
        validation_error = ValidationError(['Error 1', 'Error 2'])
        
        blog_exception = handle_django_validation_error(validation_error)
        
        self.assertIsInstance(blog_exception, ContentValidationException)
        self.assertEqual(len(blog_exception.details['errors']), 2)
        self.assertIn('Error 1', blog_exception.details['errors'])
        self.assertIn('Error 2', blog_exception.details['errors'])
    
    def test_handle_django_validation_error_single_message(self):
        """Test handling Django ValidationError with single message."""
        validation_error = ValidationError('Single error message')
        
        blog_exception = handle_django_validation_error(validation_error)
        
        self.assertIsInstance(blog_exception, ContentValidationException)
        self.assertEqual(len(blog_exception.details['errors']), 1)
        self.assertIn('Single error message', blog_exception.details['errors'])
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test getting client IP with X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        ip = get_client_ip(request)
        
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test getting client IP without X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        ip = get_client_ip(request)
        
        self.assertEqual(ip, '192.168.1.100')
    
    def test_log_security_event(self):
        """Test logging security events."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        exception = SuspiciousOperationException(
            operation="test_operation",
            ip_address="192.168.1.1"
        )
        
        # This should not raise any exceptions
        try:
            log_security_event(exception, request, self.user)
        except Exception as e:
            self.fail(f"log_security_event raised an exception: {e}")


class ExceptionInheritanceTestCase(TestCase):
    """Test exception inheritance hierarchy."""
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from appropriate base classes."""
        # Content exceptions
        self.assertIsInstance(PostNotFoundException(), ContentException)
        self.assertIsInstance(PostNotFoundException(), BlogException)
        
        # Authentication exceptions
        self.assertIsInstance(UserNotAuthenticatedException(), AuthenticationException)
        self.assertIsInstance(UserNotAuthenticatedException(), BlogException)
        
        # Comment exceptions
        self.assertIsInstance(CommentNotFoundException(), CommentException)
        self.assertIsInstance(CommentNotFoundException(), BlogException)
        
        # Rate limit exceptions
        self.assertIsInstance(RateLimitExceededException(), RateLimitException)
        self.assertIsInstance(RateLimitExceededException(), BlogException)
        
        # API exceptions
        self.assertIsInstance(InvalidAPIRequestException(), APIException)
        self.assertIsInstance(InvalidAPIRequestException(), BlogException)
        
        # File upload exceptions
        self.assertIsInstance(InvalidFileTypeException(), FileUploadException)
        self.assertIsInstance(InvalidFileTypeException(), BlogException)
        
        # Security exceptions
        self.assertIsInstance(SuspiciousOperationException(), SecurityException)
        self.assertIsInstance(SuspiciousOperationException(), BlogException)