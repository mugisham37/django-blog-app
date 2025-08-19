"""
Unit tests for enterprise_core.utils module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from enterprise_core.utils import (
    generate_unique_slug,
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


class MockModel:
    """Mock model for testing."""
    
    class objects:
        @classmethod
        def filter(cls, **kwargs):
            mock_queryset = Mock()
            # Return False for most cases to simulate unique slug
            if kwargs.get('slug') == 'existing-slug':
                mock_queryset.exists.return_value = True
            else:
                mock_queryset.exists.return_value = False
            return mock_queryset


class TestSlugGeneration:
    """Test slug generation utilities."""
    
    def test_generate_unique_slug_basic(self):
        """Test basic slug generation."""
        slug = generate_unique_slug(MockModel, "Test Title")
        assert slug == "test-title"
    
    def test_generate_unique_slug_empty_title(self):
        """Test slug generation with empty title."""
        slug = generate_unique_slug(MockModel, "")
        assert slug == "untitled"
    
    def test_generate_unique_slug_max_length(self):
        """Test slug generation with max length constraint."""
        long_title = "This is a very long title that exceeds the maximum length"
        slug = generate_unique_slug(MockModel, long_title, max_length=20)
        
        assert len(slug) <= 20
        assert slug.startswith("this-is-a-very-long")


class TestTextProcessing:
    """Test text processing utilities."""
    
    def test_calculate_reading_time_basic(self):
        """Test basic reading time calculation."""
        content = "This is a test content with exactly ten words here."
        reading_time = calculate_reading_time(content, words_per_minute=10)
        assert reading_time == 1  # 10 words at 10 wpm = 1 minute
    
    def test_calculate_reading_time_html_content(self):
        """Test reading time calculation with HTML content."""
        content = "<p>This is <strong>HTML</strong> content with <em>formatting</em>.</p>"
        reading_time = calculate_reading_time(content)
        assert reading_time > 0
    
    def test_calculate_reading_time_empty_content(self):
        """Test reading time calculation with empty content."""
        reading_time = calculate_reading_time("")
        assert reading_time == 0
    
    def test_extract_excerpt_basic(self):
        """Test basic excerpt extraction."""
        content = "This is a test content for excerpt extraction."
        excerpt = extract_excerpt(content, max_length=20)
        assert len(excerpt) <= 23  # 20 + "..."
        assert excerpt.endswith("...")
    
    def test_extract_excerpt_html_content(self):
        """Test excerpt extraction from HTML content."""
        content = "<p>This is <strong>HTML</strong> content.</p>"
        excerpt = extract_excerpt(content)
        assert "<p>" not in excerpt
        assert "<strong>" not in excerpt
        assert "This is HTML content." in excerpt
    
    def test_extract_excerpt_short_content(self):
        """Test excerpt extraction with content shorter than max_length."""
        content = "Short content."
        excerpt = extract_excerpt(content, max_length=100)
        assert excerpt == "Short content."
    
    def test_truncate_words_basic(self):
        """Test basic word truncation."""
        text = "This is a test sentence with many words."
        truncated = truncate_words(text, 5)
        assert truncated == "This is a test sentence..."
    
    def test_truncate_words_short_text(self):
        """Test word truncation with short text."""
        text = "Short text."
        truncated = truncate_words(text, 5)
        assert truncated == "Short text."
    
    def test_truncate_words_empty_text(self):
        """Test word truncation with empty text."""
        truncated = truncate_words("", 5)
        assert truncated == ""


class TestValidationUtilities:
    """Test validation utilities."""
    
    def test_is_valid_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            assert is_valid_email(email), f"Email {email} should be valid"
    
    def test_is_valid_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com',
            'user space@example.com',
            '',
            None
        ]
        
        for email in invalid_emails:
            assert not is_valid_email(email), f"Email {email} should be invalid"


class TestFileUtilities:
    """Test file-related utilities."""
    
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        size = format_file_size(512)
        assert size == "512.0 B"
    
    def test_format_file_size_kb(self):
        """Test file size formatting for kilobytes."""
        size = format_file_size(1536)  # 1.5 KB
        assert size == "1.5 KB"
    
    def test_format_file_size_mb(self):
        """Test file size formatting for megabytes."""
        size = format_file_size(1572864)  # 1.5 MB
        assert size == "1.5 MB"
    
    def test_format_file_size_zero(self):
        """Test file size formatting for zero bytes."""
        size = format_file_size(0)
        assert size == "0 B"
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        filename = sanitize_filename("test file.txt")
        assert filename == "test_file.txt"
    
    def test_sanitize_filename_special_chars(self):
        """Test filename sanitization with special characters."""
        filename = sanitize_filename("test@#$%file!.txt")
        assert filename == "test____file_.txt"
    
    def test_sanitize_filename_empty(self):
        """Test filename sanitization with empty input."""
        filename = sanitize_filename("")
        assert filename.startswith("file_")
    
    def test_sanitize_filename_path_traversal(self):
        """Test filename sanitization prevents path traversal."""
        filename = sanitize_filename("../../../etc/passwd")
        assert filename == "passwd"


class TestRandomGeneration:
    """Test random generation utilities."""
    
    def test_generate_random_string_default(self):
        """Test random string generation with defaults."""
        random_str = generate_random_string()
        assert len(random_str) == 32
        assert random_str.isalnum()
    
    def test_generate_random_string_custom_length(self):
        """Test random string generation with custom length."""
        random_str = generate_random_string(length=16)
        assert len(random_str) == 16
    
    def test_generate_random_string_lowercase_only(self):
        """Test random string generation with lowercase only."""
        random_str = generate_random_string(
            length=10,
            include_digits=False,
            include_uppercase=False
        )
        assert len(random_str) == 10
        assert random_str.islower()
        assert random_str.isalpha()


class TestSEOUtilities:
    """Test SEO-related utilities."""
    
    def test_generate_meta_title(self):
        """Test meta title generation."""
        title = generate_meta_title("My Blog Post", "My Site")
        assert title == "My Blog Post | My Site"
        
        # Test with max length
        long_title = "This is a very long title that should be truncated"
        title = generate_meta_title(long_title, max_length=30)
        assert len(title) <= 30
    
    def test_generate_meta_description(self):
        """Test meta description generation."""
        content = "This is a test content for meta description generation."
        description = generate_meta_description(content, max_length=50)
        assert len(description) <= 50
        
        # Test with HTML content
        html_content = "<p>This is <strong>HTML</strong> content.</p>"
        description = generate_meta_description(html_content)
        assert "<p>" not in description
        assert "<strong>" not in description
    
    def test_generate_meta_description_empty(self):
        """Test meta description generation with empty content."""
        description = generate_meta_description("")
        assert description == ""