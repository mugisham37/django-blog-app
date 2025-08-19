"""
Enterprise Core Validators Module

This module provides comprehensive validation functions for various types of content
including slugs, HTML content, images, emails, passwords, and more.
"""

import re
import os
from typing import Optional, List
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.conf import settings
from django.utils.html import strip_tags

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def validate_slug_format(slug: str) -> None:
    """
    Validate slug format according to URL-safe standards.
    
    Args:
        slug: The slug to validate
    
    Raises:
        ValidationError: If slug format is invalid
    """
    if not slug:
        raise ValidationError("Slug cannot be empty.")
    
    # Check for reserved words
    reserved_words = ['admin', 'api', 'blog', 'login', 'logout', 'register', 'dashboard']
    if slug.lower() in reserved_words:
        raise ValidationError(f"'{slug}' is a reserved word and cannot be used as a slug.")
    
    # Check format: only letters, numbers, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
        raise ValidationError("Slug can only contain letters, numbers, hyphens, and underscores.")
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        raise ValidationError("Slug cannot start or end with a hyphen.")
    
    # Cannot contain consecutive dots or special patterns
    if '..' in slug:
        raise ValidationError("Slug cannot contain consecutive dots.")


def validate_content_length(content: str, min_length: int = 10, max_length: int = 50000) -> None:
    """
    Validate content length (excluding HTML tags).
    
    Args:
        content: The content to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
    
    Raises:
        ValidationError: If content length is invalid
    """
    if content is None:
        raise ValidationError("Content cannot be None.")
    
    if not content.strip():
        raise ValidationError("Content cannot be empty.")
    
    # Strip HTML tags for length calculation
    clean_content = strip_tags(content).strip()
    
    if len(clean_content) < min_length:
        raise ValidationError(f"Content must be at least {min_length} characters long.")
    
    if len(clean_content) > max_length:
        raise ValidationError(f"Content cannot exceed {max_length} characters.")


def validate_html_content(content: str) -> None:
    """
    Validate HTML content for security and safety.
    
    Args:
        content: The HTML content to validate
    
    Raises:
        ValidationError: If HTML content contains dangerous elements
    """
    if not content:
        return  # Empty content is allowed
    
    # Dangerous HTML tags
    dangerous_tags = [
        'script', 'iframe', 'object', 'embed', 'form', 'input', 'button',
        'textarea', 'select', 'option', 'meta', 'link', 'style', 'base',
        'applet', 'frame', 'frameset'
    ]
    
    # Check for dangerous tags
    content_lower = content.lower()
    for tag in dangerous_tags:
        if f'<{tag}' in content_lower:
            raise ValidationError(f"HTML content cannot contain <{tag}> tags.")
    
    # Dangerous attributes
    dangerous_attributes = [
        'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset'
    ]
    
    # Check for dangerous attributes
    for attr in dangerous_attributes:
        if attr in content_lower:
            raise ValidationError(f"HTML content cannot contain '{attr}' attributes.")
    
    # Check for javascript: protocol
    if 'javascript:' in content_lower:
        raise ValidationError("HTML content cannot contain javascript: protocol.")
    
    # Check for data: protocol with HTML content
    if re.search(r'data:text/html', content_lower):
        raise ValidationError("HTML content cannot contain data:text/html protocol.")


def validate_image_file(image_file) -> None:
    """
    Validate uploaded image file.
    
    Args:
        image_file: The uploaded image file
    
    Raises:
        ValidationError: If image file is invalid
    """
    if not image_file:
        return  # Empty file is allowed
    
    if not PIL_AVAILABLE:
        # Basic validation without PIL
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = os.path.splitext(image_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(f"File extension '{file_extension}' is not allowed.")
        return
    
    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(image_file.name)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise ValidationError(f"File extension '{file_extension}' is not allowed.")
    
    # Validate file size
    max_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 5MB default
    if image_file.size > max_size:
        raise ValidationError(f"Image file size cannot exceed {max_size // (1024*1024)}MB.")
    
    try:
        # Validate image format and dimensions
        image = Image.open(image_file)
        
        # Check minimum dimensions
        min_width = getattr(settings, 'MIN_IMAGE_WIDTH', 50)
        min_height = getattr(settings, 'MIN_IMAGE_HEIGHT', 50)
        
        if image.width < min_width or image.height < min_height:
            raise ValidationError(f"Image dimensions must be at least {min_width}x{min_height} pixels.")
        
        # Check maximum dimensions
        max_width = getattr(settings, 'MAX_IMAGE_WIDTH', 4000)
        max_height = getattr(settings, 'MAX_IMAGE_HEIGHT', 4000)
        
        if image.width > max_width or image.height > max_height:
            raise ValidationError(f"Image dimensions cannot exceed {max_width}x{max_height} pixels.")
        
    except Exception as e:
        raise ValidationError(f"Invalid image file: {str(e)}")
    finally:
        # Reset file pointer
        image_file.seek(0)


def validate_email_domain(email: str) -> None:
    """
    Validate email domain against blacklists and whitelists.
    
    Args:
        email: The email address to validate
    
    Raises:
        ValidationError: If email domain is invalid
    """
    if not email:
        return
    
    # First validate email format
    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError("Invalid email format.")
    
    # Extract domain
    domain = email.split('@')[1].lower()
    
    # Check blacklisted domains
    blacklisted_domains = getattr(settings, 'BLACKLISTED_EMAIL_DOMAINS', [])
    if domain in blacklisted_domains:
        raise ValidationError(f"Email domain '{domain}' is not allowed.")
    
    # Check required domains (if specified)
    required_domains = getattr(settings, 'REQUIRED_EMAIL_DOMAINS', [])
    if required_domains and domain not in required_domains:
        raise ValidationError(f"Email must be from one of these domains: {', '.join(required_domains)}")


def validate_password_strength(password: str) -> None:
    """
    Validate password strength according to security requirements.
    
    Args:
        password: The password to validate
    
    Raises:
        ValidationError: If password is too weak
    """
    if not password:
        return  # Empty password validation handled elsewhere
    
    min_length = 8
    if len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters long.")
    
    # Check for uppercase letters
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    # Check for lowercase letters
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    
    # Check for digits
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit.")
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character.")
    
    # Check for common patterns
    common_patterns = [
        'password', '123456', 'qwerty', 'abc123', 'admin', 'letmein',
        'welcome', 'monkey', 'dragon', 'master'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            raise ValidationError(f"Password cannot contain common pattern '{pattern}'.")
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        raise ValidationError("Password cannot contain more than 2 consecutive identical characters.")


def validate_url_safety(url: str) -> None:
    """
    Validate URL for security and safety.
    
    Args:
        url: The URL to validate
    
    Raises:
        ValidationError: If URL is unsafe
    """
    if not url:
        return
    
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError("Invalid URL format.")
    
    # Check for dangerous protocols
    dangerous_protocols = ['javascript', 'data', 'vbscript', 'file', 'ftp']
    if parsed.scheme.lower() in dangerous_protocols:
        raise ValidationError(f"URL protocol '{parsed.scheme}' is not allowed.")
    
    # Only allow HTTP and HTTPS
    if parsed.scheme.lower() not in ['http', 'https']:
        raise ValidationError("Only HTTP and HTTPS URLs are allowed.")
    
    # Check for suspicious content in URL
    suspicious_patterns = [
        '<script', 'javascript:', 'eval(', 'alert(', 'confirm(',
        'prompt(', 'document.', 'window.', 'location.'
    ]
    
    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            raise ValidationError(f"URL contains suspicious content: '{pattern}'")


def validate_username_format(username: str) -> None:
    """
    Validate username format and restrictions.
    
    Args:
        username: The username to validate
    
    Raises:
        ValidationError: If username format is invalid
    """
    if not username:
        raise ValidationError("Username cannot be empty.")
    
    # Length validation
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long.")
    
    if len(username) > 30:
        raise ValidationError("Username cannot exceed 30 characters.")
    
    # Format validation: letters, numbers, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores.")
    
    # Cannot start with underscore or hyphen
    if username.startswith('_') or username.startswith('-'):
        raise ValidationError("Username cannot start with underscore or hyphen.")
    
    # Cannot contain dots
    if '.' in username:
        raise ValidationError("Username cannot contain dots.")
    
    # Check reserved usernames
    reserved_usernames = [
        'admin', 'root', 'system', 'api', 'www', 'mail', 'ftp',
        'blog', 'news', 'support', 'help', 'info', 'contact'
    ]
    
    if username.lower() in reserved_usernames:
        raise ValidationError(f"Username '{username}' is reserved and cannot be used.")


def validate_comment_content(content: str) -> None:
    """
    Validate comment content for length and spam patterns.
    
    Args:
        content: The comment content to validate
    
    Raises:
        ValidationError: If comment content is invalid
    """
    if not content or not content.strip():
        raise ValidationError("Comment content cannot be empty.")
    
    # Length validation
    clean_content = strip_tags(content).strip()
    
    if len(clean_content) < 3:
        raise ValidationError("Comment must be at least 3 characters long.")
    
    if len(clean_content) > 1000:
        raise ValidationError("Comment cannot exceed 1000 characters.")
    
    # Check for excessive URLs
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, content)
    if len(urls) > 2:
        raise ValidationError("Comment cannot contain more than 2 URLs.")
    
    # Check for excessive capitalization
    if len(re.findall(r'[A-Z]', content)) > len(content) * 0.5:
        raise ValidationError("Comment contains too much capitalization.")
    
    # Check for repeated characters
    if re.search(r'(.)\1{4,}', content):
        raise ValidationError("Comment contains too many repeated characters.")
    
    # Spam pattern detection (log but don't block)
    spam_patterns = [
        r'click here', r'buy now', r'limited time', r'amazing deal',
        r'make money', r'work from home', r'free money', r'get rich'
    ]
    
    content_lower = content.lower()
    for pattern in spam_patterns:
        if re.search(pattern, content_lower):
            # Log potential spam but don't raise ValidationError
            # In production, this would be logged to a spam detection system
            pass


def validate_tag_name(tag_name: str) -> None:
    """
    Validate tag name format and restrictions.
    
    Args:
        tag_name: The tag name to validate
    
    Raises:
        ValidationError: If tag name is invalid
    """
    if not tag_name or not tag_name.strip():
        raise ValidationError("Tag name cannot be empty.")
    
    tag_name = tag_name.strip()
    
    # Length validation
    if len(tag_name) < 2:
        raise ValidationError("Tag name must be at least 2 characters long.")
    
    if len(tag_name) > 50:
        raise ValidationError("Tag name cannot exceed 50 characters.")
    
    # Format validation: letters, numbers, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', tag_name):
        raise ValidationError("Tag name can only contain letters, numbers, spaces, hyphens, and underscores.")


def validate_category_name(category_name: str) -> None:
    """
    Validate category name format and restrictions.
    
    Args:
        category_name: The category name to validate
    
    Raises:
        ValidationError: If category name is invalid
    """
    if not category_name or not category_name.strip():
        raise ValidationError("Category name cannot be empty.")
    
    category_name = category_name.strip()
    
    # Length validation
    if len(category_name) < 2:
        raise ValidationError("Category name must be at least 2 characters long.")
    
    if len(category_name) > 100:
        raise ValidationError("Category name cannot exceed 100 characters.")
    
    # Format validation: letters, numbers, spaces, parentheses, ampersand, hyphens
    if not re.match(r'^[a-zA-Z0-9\s()&_-]+$', category_name):
        raise ValidationError("Category name contains invalid characters.")


def validate_file_upload(uploaded_file) -> None:
    """
    Validate general file upload for security.
    
    Args:
        uploaded_file: The uploaded file to validate
    
    Raises:
        ValidationError: If file upload is invalid
    """
    if not uploaded_file:
        return  # Empty file is allowed
    
    # Dangerous file extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    ]
    
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension in dangerous_extensions:
        raise ValidationError(f"File extension '{file_extension}' is not allowed for security reasons.")
    
    # Check for dangerous filenames
    dangerous_names = ['index.html', 'index.htm', '.htaccess', 'web.config']
    
    if uploaded_file.name.lower() in dangerous_names:
        raise ValidationError(f"Filename '{uploaded_file.name}' is not allowed.")
    
    # Validate file size (general limit)
    max_size = getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB default
    if uploaded_file.size > max_size:
        raise ValidationError(f"File size cannot exceed {max_size // (1024*1024)}MB.")


# Additional validation functions for specific use cases
def validate_slug_uniqueness(model_class, slug: str, exclude_id: int = None) -> None:
    """
    Validate that a slug is unique within a model.
    
    Args:
        model_class: The Django model class
        slug: The slug to validate
        exclude_id: ID to exclude from uniqueness check (for updates)
    
    Raises:
        ValidationError: If slug is not unique
    """
    queryset = model_class.objects.filter(slug=slug)
    
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    
    if queryset.exists():
        raise ValidationError(f"A {model_class.__name__.lower()} with slug '{slug}' already exists.")


def validate_json_structure(json_data: dict, required_fields: List[str] = None) -> None:
    """
    Validate JSON data structure.
    
    Args:
        json_data: The JSON data to validate
        required_fields: List of required field names
    
    Raises:
        ValidationError: If JSON structure is invalid
    """
    if not isinstance(json_data, dict):
        raise ValidationError("Data must be a valid JSON object.")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in json_data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")


# Export all validation functions
__all__ = [
    'validate_slug_format',
    'validate_content_length',
    'validate_html_content',
    'validate_image_file',
    'validate_email_domain',
    'validate_password_strength',
    'validate_url_safety',
    'validate_username_format',
    'validate_comment_content',
    'validate_tag_name',
    'validate_category_name',
    'validate_file_upload',
    'validate_slug_uniqueness',
    'validate_json_structure',
]