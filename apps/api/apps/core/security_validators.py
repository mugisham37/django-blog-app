"""
Comprehensive security validators and input sanitization for Django Personal Blog System.
Implements input validation, sanitization, and security checks.
"""

import re
import html
import logging
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator
from django.utils.html import strip_tags
from django.utils.text import slugify

logger = logging.getLogger('security')


class SecurityValidator:
    """
    Comprehensive security validator for input sanitization and validation.
    """
    
    def __init__(self):
        self.blacklisted_domains = getattr(settings, 'BLACKLISTED_EMAIL_DOMAINS', [])
        self.blacklisted_url_domains = getattr(settings, 'BLACKLISTED_URL_DOMAINS', [])
        self.inappropriate_words = getattr(settings, 'INAPPROPRIATE_WORDS', [])
        
        # Common XSS patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'onfocus\s*=',
            r'onblur\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<applet[^>]*>.*?</applet>',
            r'<meta[^>]*>',
            r'<link[^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_executesql',
            r'xp_cmdshell',
            r'--\s*$',
            r'/\*.*?\*/',
            r';\s*--',
            r';\s*/\*',
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./+',
            r'\.\.\\+',
            r'/etc/passwd',
            r'/etc/shadow',
            r'c:\\windows\\system32',
            r'%2e%2e%2f',
            r'%2e%2e\\',
            r'..%2f',
            r'..%5c',
        ]
    
    def validate_and_sanitize_text(self, text: str, max_length: int = 1000, 
                                 allow_html: bool = False) -> str:
        """
        Validate and sanitize text input.
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            
        Returns:
            Sanitized text
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")
        
        # Check length
        if len(text) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length}")
        
        # Check for inappropriate content
        self._check_inappropriate_content(text)
        
        # Check for security threats
        self._check_security_threats(text)
        
        # Sanitize based on HTML allowance
        if allow_html:
            return self._sanitize_html(text)
        else:
            return self._sanitize_plain_text(text)
    
    def validate_email(self, email: str) -> str:
        """
        Validate and sanitize email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Sanitized email
            
        Raises:
            ValidationError: If validation fails
        """
        if not email:
            raise ValidationError("Email is required")
        
        # Basic email validation
        email_validator = EmailValidator()
        email_validator(email)
        
        # Check domain blacklist
        domain = email.split('@')[1].lower()
        if domain in self.blacklisted_domains:
            raise ValidationError("Email domain is not allowed")
        
        # Check for suspicious patterns
        suspicious_patterns = ['+', '..', '--', '__']
        local_part = email.split('@')[0]
        
        for pattern in suspicious_patterns:
            if pattern in local_part:
                logger.warning(f"Suspicious email pattern detected: {email}")
        
        return email.lower().strip()
    
    def validate_url(self, url: str) -> str:
        """
        Validate and sanitize URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Sanitized URL
            
        Raises:
            ValidationError: If validation fails
        """
        if not url:
            raise ValidationError("URL is required")
        
        # Basic URL validation
        url_validator = URLValidator()
        url_validator(url)
        
        # Parse URL
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("Only HTTP and HTTPS URLs are allowed")
        
        # Check domain blacklist
        if parsed.netloc.lower() in self.blacklisted_url_domains:
            raise ValidationError("URL domain is not allowed")
        
        # Check for suspicious patterns
        if any(pattern in url.lower() for pattern in ['javascript:', 'data:', 'vbscript:']):
            raise ValidationError("Suspicious URL scheme detected")
        
        return url.strip()
    
    def validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename.
        
        Args:
            filename: Filename to validate
            
        Returns:
            Sanitized filename
            
        Raises:
            ValidationError: If validation fails
        """
        if not filename:
            raise ValidationError("Filename is required")
        
        # Check length
        if len(filename) > 255:
            raise ValidationError("Filename too long")
        
        # Check for path traversal
        if any(pattern in filename.lower() for pattern in ['../', '..\\', '/etc/', 'c:\\']):
            raise ValidationError("Invalid filename")
        
        # Check for executable extensions
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
        ]
        
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext in dangerous_extensions:
            raise ValidationError("File type not allowed")
        
        # Sanitize filename
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        return sanitized[:255]  # Ensure length limit
    
    def validate_json_data(self, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Validate and sanitize JSON data.
        
        Args:
            data: JSON data to validate
            max_depth: Maximum nesting depth
            
        Returns:
            Sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        return self._sanitize_dict(data, max_depth, 0)
    
    def _check_inappropriate_content(self, text: str) -> None:
        """Check for inappropriate content."""
        text_lower = text.lower()
        
        for word in self.inappropriate_words:
            if word.lower() in text_lower:
                logger.warning(f"Inappropriate content detected: {word}")
                raise ValidationError("Content contains inappropriate language")
    
    def _check_security_threats(self, text: str) -> None:
        """Check for security threats in text."""
        text_lower = text.lower()
        
        # Check XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"XSS pattern detected: {pattern}")
                raise ValidationError("Potentially malicious content detected")
        
        # Check SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                raise ValidationError("Potentially malicious content detected")
        
        # Check path traversal patterns
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected: {pattern}")
                raise ValidationError("Potentially malicious content detected")
    
    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML content."""
        # Allow only safe HTML tags
        allowed_tags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'code', 'pre'
        ]
        
        # Remove dangerous attributes
        dangerous_attrs = [
            'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur',
            'javascript:', 'vbscript:', 'data:', 'style'
        ]
        
        # Basic HTML sanitization (in production, use a library like bleach)
        sanitized = text
        
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous attributes
        for attr in dangerous_attrs:
            sanitized = re.sub(f'{attr}[^>]*', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _sanitize_plain_text(self, text: str) -> str:
        """Sanitize plain text."""
        # Remove HTML tags
        sanitized = strip_tags(text)
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        return sanitized.strip()
    
    def _sanitize_dict(self, data: Dict[str, Any], max_depth: int, current_depth: int) -> Dict[str, Any]:
        """Recursively sanitize dictionary data."""
        if current_depth >= max_depth:
            raise ValidationError("Data nesting too deep")
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            if not isinstance(key, str):
                continue
            
            sanitized_key = self._sanitize_plain_text(key)[:100]  # Limit key length
            
            # Sanitize value
            if isinstance(value, str):
                sanitized_value = self.validate_and_sanitize_text(value, allow_html=False)
            elif isinstance(value, dict):
                sanitized_value = self._sanitize_dict(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                sanitized_value = self._sanitize_list(value, max_depth, current_depth + 1)
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized_value = value
            else:
                # Skip unsupported types
                continue
            
            sanitized[sanitized_key] = sanitized_value
        
        return sanitized
    
    def _sanitize_list(self, data: List[Any], max_depth: int, current_depth: int) -> List[Any]:
        """Recursively sanitize list data."""
        if current_depth >= max_depth:
            raise ValidationError("Data nesting too deep")
        
        sanitized = []
        
        for item in data[:100]:  # Limit list length
            if isinstance(item, str):
                sanitized_item = self.validate_and_sanitize_text(item, allow_html=False)
            elif isinstance(item, dict):
                sanitized_item = self._sanitize_dict(item, max_depth, current_depth + 1)
            elif isinstance(item, list):
                sanitized_item = self._sanitize_list(item, max_depth, current_depth + 1)
            elif isinstance(item, (int, float, bool)) or item is None:
                sanitized_item = item
            else:
                # Skip unsupported types
                continue
            
            sanitized.append(sanitized_item)
        
        return sanitized


class PasswordValidator:
    """
    Enhanced password validation with security requirements.
    """
    
    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate(self, password: str, user=None) -> None:
        """
        Validate password against security requirements.
        
        Args:
            password: Password to validate
            user: User object for additional checks
            
        Raises:
            ValidationError: If validation fails
        """
        if not password:
            raise ValidationError("Password is required")
        
        # Length check
        if len(password) < self.min_length:
            raise ValidationError(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            raise ValidationError(f"Password must be no more than {self.max_length} characters long")
        
        # Character requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")
        
        if self.require_special and not re.search(f'[{re.escape(self.special_chars)}]', password):
            raise ValidationError("Password must contain at least one special character")
        
        # Common password check
        self._check_common_passwords(password)
        
        # User-specific checks
        if user:
            self._check_user_specific(password, user)
    
    def _check_common_passwords(self, password: str) -> None:
        """Check against common passwords."""
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            raise ValidationError("Password is too common")
    
    def _check_user_specific(self, password: str, user) -> None:
        """Check password against user-specific information."""
        if hasattr(user, 'username') and user.username.lower() in password.lower():
            raise ValidationError("Password cannot contain username")
        
        if hasattr(user, 'email') and user.email:
            email_parts = user.email.split('@')[0].lower()
            if email_parts in password.lower():
                raise ValidationError("Password cannot contain email address")
        
        if hasattr(user, 'first_name') and user.first_name:
            if user.first_name.lower() in password.lower():
                raise ValidationError("Password cannot contain first name")
        
        if hasattr(user, 'last_name') and user.last_name:
            if user.last_name.lower() in password.lower():
                raise ValidationError("Password cannot contain last name")


# Utility functions

def sanitize_user_input(data: Union[str, Dict, List], allow_html: bool = False) -> Union[str, Dict, List]:
    """
    Sanitize user input data.
    
    Args:
        data: Data to sanitize
        allow_html: Whether to allow HTML in strings
        
    Returns:
        Sanitized data
    """
    validator = SecurityValidator()
    
    if isinstance(data, str):
        return validator.validate_and_sanitize_text(data, allow_html=allow_html)
    elif isinstance(data, dict):
        return validator.validate_json_data(data)
    elif isinstance(data, list):
        return validator._sanitize_list(data, 10, 0)
    else:
        return data


def validate_file_upload(file) -> None:
    """
    Validate uploaded file for security.
    
    Args:
        file: Uploaded file object
        
    Raises:
        ValidationError: If validation fails
    """
    validator = SecurityValidator()
    
    # Validate filename
    validator.validate_filename(file.name)
    
    # Check file size
    max_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
    if file.size > max_size:
        raise ValidationError(f"File size exceeds maximum of {max_size} bytes")
    
    # Check file type
    allowed_types = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', ['.jpg', '.png', '.pdf'])
    file_ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
    
    if file_ext not in allowed_types:
        raise ValidationError(f"File type {file_ext} is not allowed")


def check_rate_limit(identifier: str, limit: int, window: int) -> bool:
    """
    Check if rate limit is exceeded.
    
    Args:
        identifier: Unique identifier for rate limiting
        limit: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        True if rate limit exceeded, False otherwise
    """
    from django.core.cache import cache
    
    key = f"rate_limit:{identifier}"
    current = cache.get(key, 0)
    
    if current >= limit:
        return True
    
    # Increment counter
    cache.set(key, current + 1, window)
    return False