"""
Enterprise Core Package

This package provides core business logic, utilities, exceptions, validators,
and common patterns for the enterprise application.
"""

__version__ = "1.0.0"
__author__ = "Enterprise Development Team"

# Import main components for easy access
from .exceptions import (
    BusinessLogicError,
    ValidationError,
    AuthenticationError,
    ContentError,
    RateLimitExceededException,
)

from .utils import (
    generate_unique_slug,
    generate_slug_with_validation,
    calculate_reading_time,
    extract_excerpt,
    truncate_words,
    is_valid_email,
    format_file_size,
    generate_random_string,
    sanitize_filename,
    generate_meta_title,
    generate_meta_description,
)

from .validators import (
    validate_slug_format,
    validate_content_length,
    validate_html_content,
    validate_password_strength,
    validate_email_domain,
)

from .decorators import (
    require_authentication,
    require_permission,
    require_role,
    rate_limit,
    validate_content_security,
    cache_result,
)

__all__ = [
    # Exceptions
    'BusinessLogicError',
    'ValidationError', 
    'AuthenticationError',
    'ContentError',
    'RateLimitExceededException',
    
    # Utils
    'generate_unique_slug',
    'generate_slug_with_validation',
    'calculate_reading_time',
    'extract_excerpt',
    'truncate_words',
    'is_valid_email',
    'format_file_size',
    'generate_random_string',
    'sanitize_filename',
    'generate_meta_title',
    'generate_meta_description',
    
    # Validators
    'validate_slug_format',
    'validate_content_length',
    'validate_html_content',
    'validate_password_strength',
    'validate_email_domain',
    
    # Decorators
    'require_authentication',
    'require_permission',
    'require_role',
    'rate_limit',
    'validate_content_security',
    'cache_result',
]