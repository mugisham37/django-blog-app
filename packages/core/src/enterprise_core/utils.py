"""
Enterprise Core Utilities Module

This module provides utility functions for common operations like slug generation,
image processing, text manipulation, email handling, and more.
"""

import hashlib
import os
import re
import string
import secrets
from datetime import datetime
from typing import Optional, Union, Dict, Any, List
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.conf import settings
from django.utils.html import strip_tags

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


def generate_unique_slug(model_class, title: str, slug_field: str = 'slug', max_length: int = 50) -> str:
    """
    Generate a unique slug for a model instance.
    
    Args:
        model_class: The Django model class
        title: The title to generate slug from
        slug_field: The field name for the slug (default: 'slug')
        max_length: Maximum length of the slug
    
    Returns:
        A unique slug string
    """
    if not title.strip():
        base_slug = "untitled"
    else:
        base_slug = slugify(title)[:max_length]
    
    if not base_slug:
        base_slug = "untitled"
    
    slug = base_slug
    counter = 1
    
    # Check for existing slugs and increment counter if needed
    while model_class.objects.filter(**{slug_field: slug}).exists():
        suffix = f"-{counter}"
        max_base_length = max_length - len(suffix)
        slug = f"{base_slug[:max_base_length]}{suffix}"
        counter += 1
    
    return slug


def generate_slug_with_validation(title: str, max_length: int = 50) -> str:
    """
    Generate a slug with validation and cleanup.
    
    Args:
        title: The title to generate slug from
        max_length: Maximum length of the slug
    
    Returns:
        A validated slug string
    """
    if not title.strip():
        return "untitled"
    
    # Basic slug generation
    slug = slugify(title)[:max_length]
    
    # Ensure slug is not empty after slugification
    if not slug:
        return "untitled"
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure slug doesn't start with a number (optional validation)
    if slug and slug[0].isdigit():
        slug = f"post-{slug}"
    
    return slug[:max_length]


def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time for content.
    
    Args:
        content: The content to analyze
        words_per_minute: Average reading speed (default: 200 WPM)
    
    Returns:
        Estimated reading time in minutes
    """
    if not content:
        return 0
    
    # Strip HTML tags if present
    clean_content = strip_tags(content)
    
    # Count words
    words = len(clean_content.split())
    
    # Calculate reading time (minimum 1 minute)
    reading_time = max(1, round(words / words_per_minute))
    
    return reading_time


def extract_excerpt(content: str, max_length: int = 150, end_with_sentence: bool = False) -> str:
    """
    Extract an excerpt from content.
    
    Args:
        content: The content to extract from
        max_length: Maximum length of excerpt
        end_with_sentence: Whether to end at sentence boundary
    
    Returns:
        Excerpt string
    """
    if not content:
        return ""
    
    # Strip HTML tags
    clean_content = strip_tags(content).strip()
    
    if len(clean_content) <= max_length:
        return clean_content
    
    if end_with_sentence:
        # Try to end at sentence boundary
        sentences = re.split(r'[.!?]+', clean_content)
        excerpt = ""
        for sentence in sentences:
            if len(excerpt + sentence + ".") <= max_length:
                excerpt += sentence + "."
            else:
                break
        
        if excerpt:
            return excerpt.strip()
    
    # Truncate at word boundary
    words = clean_content[:max_length].split()
    if len(clean_content) > max_length:
        words = words[:-1]  # Remove potentially truncated last word
        return " ".join(words) + "..."
    
    return clean_content


def send_notification_email(recipient_email: str, subject: str, template_name: str, 
                          context: Dict[str, Any] = None, from_email: str = None) -> bool:
    """
    Send a notification email using a template.
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject
        template_name: Template name for email content
        context: Template context variables
        from_email: Sender email (uses default if None)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        if context is None:
            context = {}
        
        # Render email content from template
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = render_to_string(f'emails/{template_name}.txt', context)
        
        # Send email
        success = send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False
        )
        
        return bool(success)
    
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Failed to send email to {recipient_email}: {e}")
        return False


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        MD5 hash as cache key
    """
    # Convert arguments to strings
    key_parts = []
    
    for arg in args:
        if hasattr(arg, 'id') and hasattr(arg, '__class__'):
            # Handle model instances
            key_parts.append(f"{arg.__class__.__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}:{value}")
    
    # Create hash
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return f"file_{generate_random_string(8)}"
    
    # Remove path components (prevent directory traversal)
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    safe_chars = string.ascii_letters + string.digits + '.-_'
    sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # Ensure filename is not empty
    if not sanitized or sanitized.startswith('.'):
        sanitized = f"file_{generate_random_string(8)}.txt"
    
    return sanitized


def get_file_upload_path(instance, filename: str) -> str:
    """
    Generate upload path for file uploads.
    
    Args:
        instance: Model instance
        filename: Original filename
    
    Returns:
        Upload path string
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Generate path with date structure
    now = datetime.now()
    date_path = now.strftime('%Y/%m/%d')
    
    # Use model name in path
    model_name = instance.__class__.__name__.lower()
    
    return f"uploads/{model_name}/{date_path}/{safe_filename}"


def truncate_words(text: str, word_count: int) -> str:
    """
    Truncate text to specified word count.
    
    Args:
        text: Text to truncate
        word_count: Maximum number of words
    
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= word_count:
        return text
    
    return " ".join(words[:word_count]) + "..."


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
    
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def clean_html_content(content: str) -> str:
    """
    Clean HTML content to prevent XSS attacks.
    
    Args:
        content: HTML content to clean
    
    Returns:
        Cleaned HTML content
    """
    if not content:
        return ""
    
    if BLEACH_AVAILABLE:
        # Use bleach for comprehensive HTML cleaning
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote',
            'a', 'img', 'code', 'pre'
        ]
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        
        return bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    else:
        # Fallback: return content as-is (should implement basic cleaning)
        return content


def generate_random_string(length: int = 32, include_digits: bool = True, 
                         include_uppercase: bool = True) -> str:
    """
    Generate a random string.
    
    Args:
        length: Length of the string
        include_digits: Whether to include digits
        include_uppercase: Whether to include uppercase letters
    
    Returns:
        Random string
    """
    chars = string.ascii_lowercase
    
    if include_uppercase:
        chars += string.ascii_uppercase
    
    if include_digits:
        chars += string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


# Image Processing Functions
def process_uploaded_image(image_file, max_width: int = 1200, max_height: int = 800, 
                         quality: int = 85, format: str = 'JPEG') -> Optional[ContentFile]:
    """
    Process uploaded image: resize, optimize, and convert format.
    
    Args:
        image_file: Uploaded image file
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)
        format: Output format (JPEG, PNG, etc.)
    
    Returns:
        Processed image as ContentFile or None if processing failed
    """
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Open image
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if saving as JPEG
        if format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if necessary
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save processed image
        output = BytesIO()
        save_kwargs = {'format': format}
        
        if format == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        return ContentFile(output.getvalue())
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def create_thumbnail(image_file, size: tuple = (150, 150), crop: bool = True) -> Optional[ContentFile]:
    """
    Create a thumbnail from an image.
    
    Args:
        image_file: Source image file
        size: Thumbnail size as (width, height)
        crop: Whether to crop to exact size or maintain aspect ratio
    
    Returns:
        Thumbnail as ContentFile or None if creation failed
    """
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Open image
        image = Image.open(image_file)
        
        if crop:
            # Crop to exact size
            image = image.resize(size, Image.Resampling.LANCZOS)
        else:
            # Maintain aspect ratio
            image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save thumbnail
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        return ContentFile(output.getvalue())
    
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None


# SEO and Meta Functions (referenced in tests)
def generate_meta_title(title: str, site_name: str = None, max_length: int = 60) -> str:
    """Generate SEO-optimized meta title."""
    if not title:
        return site_name or "Blog"
    
    if site_name and title != site_name:
        full_title = f"{title} | {site_name}"
    else:
        full_title = title
    
    return full_title[:max_length]


def generate_meta_description(content: str, max_length: int = 160) -> str:
    """Generate SEO-optimized meta description."""
    if not content:
        return ""
    
    # Extract clean text and create description
    clean_text = strip_tags(content).strip()
    
    if len(clean_text) <= max_length:
        return clean_text
    
    # Truncate at word boundary
    words = clean_text[:max_length].split()
    words = words[:-1]  # Remove potentially truncated last word
    return " ".join(words) + "..."


def extract_keywords_from_content(content: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from content for SEO."""
    if not content:
        return []
    
    # Clean content
    clean_text = strip_tags(content).lower()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text)
    
    # Filter stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def calculate_enhanced_reading_time(content: str, words_per_minute: int = 200) -> Dict[str, Any]:
    """Calculate enhanced reading time with additional metrics."""
    if not content:
        return {
            'reading_time': 0,
            'word_count': 0,
            'character_count': 0,
            'paragraph_count': 0
        }
    
    clean_content = strip_tags(content)
    words = clean_content.split()
    
    return {
        'reading_time': max(1, round(len(words) / words_per_minute)),
        'word_count': len(words),
        'character_count': len(clean_content),
        'paragraph_count': len([p for p in content.split('\n\n') if p.strip()])
    }


def validate_seo_content(title: str, content: str, meta_description: str = None) -> Dict[str, Any]:
    """Validate content for SEO best practices."""
    issues = []
    recommendations = []
    
    # Title validation
    if not title:
        issues.append("Title is missing")
    elif len(title) < 30:
        recommendations.append("Title could be longer (30-60 characters recommended)")
    elif len(title) > 60:
        issues.append("Title is too long (over 60 characters)")
    
    # Content validation
    if not content:
        issues.append("Content is missing")
    else:
        word_count = len(strip_tags(content).split())
        if word_count < 300:
            recommendations.append("Content could be longer (300+ words recommended)")
    
    # Meta description validation
    if meta_description:
        if len(meta_description) > 160:
            issues.append("Meta description is too long (over 160 characters)")
        elif len(meta_description) < 120:
            recommendations.append("Meta description could be longer (120-160 characters recommended)")
    else:
        recommendations.append("Meta description is missing")
    
    return {
        'issues': issues,
        'recommendations': recommendations,
        'seo_score': max(0, 100 - len(issues) * 20 - len(recommendations) * 5)
    }


# Export all functions
__all__ = [
    # Slug and text utilities
    'generate_unique_slug',
    'generate_slug_with_validation',
    'calculate_reading_time',
    'extract_excerpt',
    'truncate_words',
    'clean_html_content',
    
    # Email utilities
    'send_notification_email',
    'is_valid_email',
    
    # Cache utilities
    'generate_cache_key',
    
    # File utilities
    'sanitize_filename',
    'get_file_upload_path',
    'format_file_size',
    
    # Image processing
    'process_uploaded_image',
    'create_thumbnail',
    
    # Network utilities
    'get_client_ip',
    
    # Random generation
    'generate_random_string',
    
    # SEO utilities
    'generate_meta_title',
    'generate_meta_description',
    'extract_keywords_from_content',
    'calculate_enhanced_reading_time',
    'validate_seo_content',
]