"""
Enterprise Core Exceptions Module

This module provides a comprehensive exception hierarchy for the enterprise application.
All exceptions inherit from a base BlogException class and provide structured error information.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from django.core.exceptions import ValidationError as DjangoValidationError

logger = logging.getLogger(__name__)


class BusinessLogicError(Exception):
    """Base exception for business logic errors"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details
        }


# Alias for backward compatibility
BlogException = BusinessLogicError


class ValidationError(BusinessLogicError):
    """Validation-specific errors"""
    pass


class AuthenticationError(BusinessLogicError):
    """Authentication-specific errors"""
    pass


class ContentError(BusinessLogicError):
    """Content-related errors"""
    pass


# Content Exceptions
class ContentException(ContentError):
    """Base class for content-related exceptions."""
    pass


class PostNotFoundException(ContentException):
    """Exception raised when a post is not found."""
    
    def __init__(self, post_id: int = None, slug: str = None, message: str = None):
        if message is None:
            if post_id:
                message = f"Post with ID {post_id} not found"
            elif slug:
                message = f"Post with slug '{slug}' not found"
            else:
                message = "Post not found"
        
        details = {}
        if post_id:
            details['post_id'] = post_id
        if slug:
            details['slug'] = slug
            
        super().__init__(message, code="POST_NOT_FOUND", details=details)


class PostNotPublishedException(ContentException):
    """Exception raised when trying to access an unpublished post."""
    
    def __init__(self, post_id: int = None, status: str = None, message: str = None):
        if message is None:
            message = f"Post {post_id or ''} is not published"
            if status:
                message += f" (status: {status})"
        
        details = {}
        if post_id:
            details['post_id'] = post_id
        if status:
            details['status'] = status
            
        super().__init__(message, code="POST_NOT_PUBLISHED", details=details)


class CategoryNotFoundException(ContentException):
    """Exception raised when a category is not found."""
    
    def __init__(self, category_id: int = None, slug: str = None, message: str = None):
        if message is None:
            if category_id:
                message = f"Category with ID {category_id} not found"
            elif slug:
                message = f"Category with slug '{slug}' not found"
            else:
                message = "Category not found"
        
        details = {}
        if category_id:
            details['category_id'] = category_id
        if slug:
            details['slug'] = slug
            
        super().__init__(message, code="CATEGORY_NOT_FOUND", details=details)


class TagNotFoundException(ContentException):
    """Exception raised when a tag is not found."""
    
    def __init__(self, tag_id: int = None, slug: str = None, message: str = None):
        if message is None:
            if tag_id:
                message = f"Tag with ID {tag_id} not found"
            elif slug:
                message = f"Tag with slug '{slug}' not found"
            else:
                message = "Tag not found"
        
        details = {}
        if tag_id:
            details['tag_id'] = tag_id
        if slug:
            details['slug'] = slug
            
        super().__init__(message, code="TAG_NOT_FOUND", details=details)


class ContentValidationException(ContentException):
    """Exception raised when content validation fails."""
    
    def __init__(self, field: str = None, errors: List[str] = None, message: str = None):
        if message is None:
            if field:
                message = f"Content validation failed for field '{field}'"
            else:
                message = "Content validation failed"
        
        details = {}
        if field:
            details['field'] = field
        if errors:
            details['errors'] = errors
            
        super().__init__(message, code="CONTENT_VALIDATION_ERROR", details=details)


class DuplicateSlugException(ContentException):
    """Exception raised when a duplicate slug is detected."""
    
    def __init__(self, slug: str, model_name: str = None, message: str = None):
        if message is None:
            message = f"Duplicate slug '{slug}'"
            if model_name:
                message += f" for {model_name}"
        
        details = {'slug': slug}
        if model_name:
            details['model'] = model_name
            
        super().__init__(message, code="DUPLICATE_SLUG", details=details)


# Authentication Exceptions
class AuthenticationException(AuthenticationError):
    """Base class for authentication-related exceptions."""
    pass


class UserNotAuthenticatedException(AuthenticationException):
    """Exception raised when user authentication is required."""
    
    def __init__(self, required_action: str = None, message: str = None):
        if message is None:
            message = "Authentication required"
            if required_action:
                message += f" to {required_action}"
        
        details = {}
        if required_action:
            details['required_action'] = required_action
            
        super().__init__(message, code="AUTHENTICATION_REQUIRED", details=details)


class InsufficientPermissionsException(AuthenticationException):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, required_permission: str = None, user_permissions: List[str] = None, message: str = None):
        if message is None:
            message = "Insufficient permissions"
            if required_permission:
                message += f" (required: {required_permission})"
        
        details = {}
        if required_permission:
            details['required_permission'] = required_permission
        if user_permissions:
            details['user_permissions'] = user_permissions
            
        super().__init__(message, code="INSUFFICIENT_PERMISSIONS", details=details)


class InvalidTokenException(AuthenticationException):
    """Exception raised when a token is invalid or expired."""
    
    def __init__(self, token_type: str = None, message: str = None):
        if message is None:
            message = "Token is invalid or expired"
            if token_type:
                message = f"{token_type} token is invalid or expired"
        
        details = {}
        if token_type:
            details['token_type'] = token_type
            
        super().__init__(message, code="INVALID_TOKEN", details=details)


class AccountLockedException(AuthenticationException):
    """Exception raised when an account is locked."""
    
    def __init__(self, username: str = None, lock_reason: str = None, message: str = None):
        if message is None:
            message = "Account is locked"
            if lock_reason:
                message += f": {lock_reason}"
        
        details = {}
        if username:
            details['username'] = username
        if lock_reason:
            details['lock_reason'] = lock_reason
            
        super().__init__(message, code="ACCOUNT_LOCKED", details=details)


# Comment Exceptions
class CommentException(BusinessLogicError):
    """Base class for comment-related exceptions."""
    pass


class CommentNotFoundException(CommentException):
    """Exception raised when a comment is not found."""
    
    def __init__(self, comment_id: int = None, message: str = None):
        if message is None:
            message = f"Comment with ID {comment_id} not found" if comment_id else "Comment not found"
        
        details = {}
        if comment_id:
            details['comment_id'] = comment_id
            
        super().__init__(message, code="COMMENT_NOT_FOUND", details=details)


class CommentModerationException(CommentException):
    """Exception raised when comment moderation fails."""
    
    def __init__(self, comment_id: int = None, reason: str = None, message: str = None):
        if message is None:
            message = "Comment moderation failed"
            if reason:
                message += f": {reason}"
        
        details = {}
        if comment_id:
            details['comment_id'] = comment_id
        if reason:
            details['reason'] = reason
            
        super().__init__(message, code="COMMENT_MODERATION_FAILED", details=details)


class SpamDetectedException(CommentException):
    """Exception raised when spam is detected."""
    
    def __init__(self, content_type: str = None, spam_score: float = None, message: str = None):
        if message is None:
            message = "Spam detected"
            if content_type:
                message += f" in {content_type}"
        
        details = {}
        if content_type:
            details['content_type'] = content_type
        if spam_score:
            details['spam_score'] = spam_score
            
        super().__init__(message, code="SPAM_DETECTED", details=details)


# Rate Limiting Exceptions
class RateLimitException(BusinessLogicError):
    """Base class for rate limiting exceptions."""
    pass


class RateLimitExceededException(RateLimitException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, limit_type: str = None, retry_after: int = None, message: str = None):
        if message is None:
            message = "Rate limit exceeded"
            if limit_type:
                message += f" for {limit_type}"
            if retry_after:
                message += f". Try again in {retry_after} seconds"
        
        details = {}
        if limit_type:
            details['limit_type'] = limit_type
        if retry_after:
            details['retry_after'] = retry_after
            
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)


# API Exceptions
class APIException(BusinessLogicError):
    """Base class for API-related exceptions."""
    pass


class InvalidAPIRequestException(APIException):
    """Exception raised for invalid API requests."""
    
    def __init__(self, field: str = None, errors: List[str] = None, message: str = None):
        if message is None:
            message = "Invalid API request"
            if field:
                message += f" for field '{field}'"
        
        details = {}
        if field:
            details['field'] = field
        if errors:
            details['errors'] = errors
            
        super().__init__(message, code="INVALID_API_REQUEST", details=details)


class APIVersionNotSupportedException(APIException):
    """Exception raised when API version is not supported."""
    
    def __init__(self, requested_version: str = None, supported_versions: List[str] = None, message: str = None):
        if message is None:
            message = f"API version {requested_version} is not supported"
            if supported_versions:
                message += f". Supported versions: {', '.join(supported_versions)}"
        
        details = {}
        if requested_version:
            details['requested_version'] = requested_version
        if supported_versions:
            details['supported_versions'] = supported_versions
            
        super().__init__(message, code="API_VERSION_NOT_SUPPORTED", details=details)


# File Upload Exceptions
class FileUploadException(BusinessLogicError):
    """Base class for file upload exceptions."""
    pass


class InvalidFileTypeException(FileUploadException):
    """Exception raised when file type is not allowed."""
    
    def __init__(self, file_type: str = None, allowed_types: List[str] = None, message: str = None):
        if message is None:
            message = f"File type {file_type} is not allowed"
            if allowed_types:
                message += f". Allowed types: {', '.join(allowed_types)}"
        
        details = {}
        if file_type:
            details['file_type'] = file_type
        if allowed_types:
            details['allowed_types'] = allowed_types
            
        super().__init__(message, code="INVALID_FILE_TYPE", details=details)


class FileSizeExceededException(FileUploadException):
    """Exception raised when file size exceeds limit."""
    
    def __init__(self, file_size: float = None, max_size: float = None, message: str = None):
        if message is None:
            message = "File size exceeds maximum allowed size"
            if file_size and max_size:
                message = f"File size {file_size}MB exceeds maximum allowed size of {max_size}MB"
        
        details = {}
        if file_size:
            details['file_size'] = file_size
        if max_size:
            details['max_size'] = max_size
            
        super().__init__(message, code="FILE_SIZE_EXCEEDED", details=details)


# Security Exceptions
class SecurityException(BusinessLogicError):
    """Base class for security-related exceptions."""
    pass


class SuspiciousOperationException(SecurityException):
    """Exception raised for suspicious operations."""
    
    def __init__(self, operation: str = None, user_id: int = None, ip_address: str = None, message: str = None):
        if message is None:
            message = "Suspicious operation detected"
            if operation:
                message += f": {operation}"
        
        details = {}
        if operation:
            details['operation'] = operation
        if user_id:
            details['user_id'] = user_id
        if ip_address:
            details['ip_address'] = ip_address
            
        super().__init__(message, code="SUSPICIOUS_OPERATION", details=details)


class CSRFException(SecurityException):
    """Exception raised for CSRF validation failures."""
    
    def __init__(self, request_path: str = None, message: str = None):
        if message is None:
            message = "CSRF validation failed"
            if request_path:
                message += f" for {request_path}"
        
        details = {}
        if request_path:
            details['request_path'] = request_path
            
        super().__init__(message, code="CSRF_FAILED", details=details)


class XSSAttemptException(SecurityException):
    """Exception raised when XSS attempt is detected."""
    
    def __init__(self, content: str = None, field: str = None, message: str = None):
        if message is None:
            message = "XSS attempt detected"
            if field:
                message += f" in field '{field}'"
        
        details = {}
        if content:
            # Truncate content for security logging
            details['content'] = content[:100] if len(content) > 100 else content
        if field:
            details['field'] = field
            
        super().__init__(message, code="XSS_ATTEMPT", details=details)


# Utility Functions
def handle_django_validation_error(validation_error: DjangoValidationError) -> ContentValidationException:
    """Convert Django ValidationError to ContentValidationException."""
    errors = []
    
    if hasattr(validation_error, 'error_dict'):
        # Handle ValidationError with error_dict
        for field, field_errors in validation_error.error_dict.items():
            for error in field_errors:
                errors.append(str(error))
    elif hasattr(validation_error, 'error_list'):
        # Handle ValidationError with error_list
        for error in validation_error.error_list:
            errors.append(str(error))
    else:
        # Handle single message
        errors.append(str(validation_error))
    
    return ContentValidationException(errors=errors)


def get_client_ip(request) -> str:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_security_event(exception: SecurityException, request=None, user=None):
    """Log security events for monitoring and analysis."""
    log_data = {
        'exception_type': exception.__class__.__name__,
        'message': exception.message,
        'code': exception.code,
        'details': exception.details,
    }
    
    if request:
        log_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
        })
    
    if user and hasattr(user, 'id'):
        log_data['user_id'] = user.id
        log_data['username'] = getattr(user, 'username', '')
    
    logger.warning(f"Security event: {exception.__class__.__name__}", extra=log_data)


# Export all exceptions and utilities
__all__ = [
    # Base exceptions
    'BusinessLogicError',
    'BlogException',
    'ValidationError',
    'AuthenticationError',
    'ContentError',
    
    # Content exceptions
    'ContentException',
    'PostNotFoundException',
    'PostNotPublishedException',
    'CategoryNotFoundException',
    'TagNotFoundException',
    'ContentValidationException',
    'DuplicateSlugException',
    
    # Authentication exceptions
    'AuthenticationException',
    'UserNotAuthenticatedException',
    'InsufficientPermissionsException',
    'InvalidTokenException',
    'AccountLockedException',
    
    # Comment exceptions
    'CommentException',
    'CommentNotFoundException',
    'CommentModerationException',
    'SpamDetectedException',
    
    # Rate limiting exceptions
    'RateLimitException',
    'RateLimitExceededException',
    
    # API exceptions
    'APIException',
    'InvalidAPIRequestException',
    'APIVersionNotSupportedException',
    
    # File upload exceptions
    'FileUploadException',
    'InvalidFileTypeException',
    'FileSizeExceededException',
    
    # Security exceptions
    'SecurityException',
    'SuspiciousOperationException',
    'CSRFException',
    'XSSAttemptException',
    
    # Utility functions
    'handle_django_validation_error',
    'get_client_ip',
    'log_security_event',
]