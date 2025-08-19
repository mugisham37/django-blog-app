"""
Unit tests for enterprise_core.validators module.
"""

import pytest
from django.core.exceptions import ValidationError

from enterprise_core.validators import (
    validate_slug_format,
    validate_content_length,
    validate_html_content,
    validate_email_domain,
    validate_password_strength,
    validate_url_safety,
    validate_username_format,
    validate_comment_content,
    validate_tag_name,
    validate_category_name,
)


class TestSlugValidation:
    """Test slug format validation."""
    
    def test_valid_slugs(self):
        """Test valid slug formats."""
        valid_slugs = [
            'hello-world',
            'test_slug',
            'slug123',
            'a',
            'test-123_slug'
        ]
        
        for slug in valid_slugs:
            try:
                validate_slug_format(slug)
            except ValidationError:
                pytest.fail(f"Valid slug '{slug}' raised ValidationError")
    
    def test_invalid_slugs(self):
        """Test invalid slug formats."""
        invalid_slugs = [
            '',  # Empty
            'hello world',  # Spaces
            'hello@world',  # Special characters
            '-hello',  # Starts with hyphen
            'hello-',  # Ends with hyphen
            'hello..world',  # Double dots
        ]
        
        for slug in invalid_slugs:
            with pytest.raises(ValidationError):
                validate_slug_format(slug)
    
    def test_reserved_words(self):
        """Test reserved word validation."""
        reserved_words = ['admin', 'api', 'blog', 'login']
        
        for word in reserved_words:
            with pytest.raises(ValidationError):
                validate_slug_format(word)


class TestContentValidation:
    """Test content length validation."""
    
    def test_valid_content_length(self):
        """Test valid content lengths."""
        valid_content = "This is a valid content with sufficient length."
        
        try:
            validate_content_length(valid_content)
        except ValidationError:
            pytest.fail("Valid content raised ValidationError")
    
    def test_content_too_short(self):
        """Test content that is too short."""
        short_content = "Short"
        
        with pytest.raises(ValidationError):
            validate_content_length(short_content)
    
    def test_content_too_long(self):
        """Test content that is too long."""
        long_content = "x" * 60000
        
        with pytest.raises(ValidationError):
            validate_content_length(long_content)
    
    def test_html_content_length(self):
        """Test content length calculation with HTML tags."""
        html_content = "<p>This is a valid content with sufficient length.</p>"
        
        try:
            validate_content_length(html_content)
        except ValidationError:
            pytest.fail("Valid HTML content raised ValidationError")
    
    def test_empty_content(self):
        """Test empty content validation."""
        with pytest.raises(ValidationError):
            validate_content_length("")
        
        with pytest.raises(ValidationError):
            validate_content_length(None)


class TestHTMLValidation:
    """Test HTML content validation."""
    
    def test_safe_html_content(self):
        """Test safe HTML content."""
        safe_html = "<p>This is <strong>safe</strong> HTML content.</p>"
        
        try:
            validate_html_content(safe_html)
        except ValidationError:
            pytest.fail("Safe HTML content raised ValidationError")
    
    def test_dangerous_tags(self):
        """Test dangerous HTML tags."""
        dangerous_html_samples = [
            "<script>alert('xss')</script>",
            "<iframe src='malicious.com'></iframe>",
            "<form><input type='text'></form>",
            "<object data='malicious.swf'></object>",
        ]
        
        for html in dangerous_html_samples:
            with pytest.raises(ValidationError):
                validate_html_content(html)
    
    def test_dangerous_attributes(self):
        """Test dangerous HTML attributes."""
        dangerous_html_samples = [
            "<div onclick='alert(1)'>Click me</div>",
            "<img src='x' onerror='alert(1)'>",
            "<a href='javascript:alert(1)'>Link</a>",
            "<div onload='malicious()'>Content</div>",
        ]
        
        for html in dangerous_html_samples:
            with pytest.raises(ValidationError):
                validate_html_content(html)
    
    def test_empty_html_content(self):
        """Test empty HTML content."""
        try:
            validate_html_content("")
            validate_html_content(None)
        except ValidationError:
            pytest.fail("Empty HTML content should not raise ValidationError")


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_strong_password(self):
        """Test strong password."""
        strong_password = "StrongP@ssw0rd123"
        
        try:
            validate_password_strength(strong_password)
        except ValidationError:
            pytest.fail("Strong password raised ValidationError")
    
    def test_weak_passwords(self):
        """Test weak passwords."""
        weak_passwords = [
            'short',  # Too short
            'alllowercase',  # No uppercase
            'ALLUPPERCASE',  # No lowercase
            'NoNumbers!',  # No digits
            'NoSpecial123',  # No special characters
            'password123',  # Common pattern
            'aaabbbccc',  # Repeated characters
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                validate_password_strength(password)
    
    def test_empty_password(self):
        """Test empty password."""
        try:
            validate_password_strength("")
            validate_password_strength(None)
        except ValidationError:
            pytest.fail("Empty password should not raise ValidationError")


class TestURLValidation:
    """Test URL safety validation."""
    
    def test_safe_urls(self):
        """Test safe URLs."""
        safe_urls = [
            'https://example.com',
            'http://blog.example.org/post/123',
            'https://subdomain.example.com/path?param=value',
        ]
        
        for url in safe_urls:
            try:
                validate_url_safety(url)
            except ValidationError:
                pytest.fail(f"Safe URL '{url}' raised ValidationError")
    
    def test_dangerous_protocols(self):
        """Test dangerous URL protocols."""
        dangerous_urls = [
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            'vbscript:msgbox(1)',
            'file:///etc/passwd',
        ]
        
        for url in dangerous_urls:
            with pytest.raises(ValidationError):
                validate_url_safety(url)
    
    def test_suspicious_content(self):
        """Test URLs with suspicious content."""
        suspicious_urls = [
            'https://example.com/<script>alert(1)</script>',
            'https://example.com/?param=javascript:alert(1)',
            'https://example.com/eval(malicious)',
        ]
        
        for url in suspicious_urls:
            with pytest.raises(ValidationError):
                validate_url_safety(url)


class TestUsernameValidation:
    """Test username format validation."""
    
    def test_valid_usernames(self):
        """Test valid username formats."""
        valid_usernames = [
            'user123',
            'test_user',
            'user-name',
            'username',
        ]
        
        for username in valid_usernames:
            try:
                validate_username_format(username)
            except ValidationError:
                pytest.fail(f"Valid username '{username}' raised ValidationError")
    
    def test_invalid_usernames(self):
        """Test invalid username formats."""
        invalid_usernames = [
            '',  # Empty
            'ab',  # Too short
            'a' * 31,  # Too long
            'user name',  # Spaces
            'user@name',  # Special characters
            '_username',  # Starts with underscore
            'user.name',  # Contains dot
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValidationError):
                validate_username_format(username)
    
    def test_reserved_usernames(self):
        """Test reserved username validation."""
        reserved_usernames = ['admin', 'root', 'system', 'api']
        
        for username in reserved_usernames:
            with pytest.raises(ValidationError):
                validate_username_format(username)


class TestCommentValidation:
    """Test comment content validation."""
    
    def test_valid_comment(self):
        """Test valid comment content."""
        valid_comment = "This is a valid comment with sufficient content."
        
        try:
            validate_comment_content(valid_comment)
        except ValidationError:
            pytest.fail("Valid comment raised ValidationError")
    
    def test_invalid_comments(self):
        """Test invalid comment content."""
        invalid_comments = [
            '',  # Empty
            'Hi',  # Too short
            'x' * 1001,  # Too long
            'Check out http://spam1.com and http://spam2.com and http://spam3.com',  # Too many URLs
            'BUY NOW!!! AMAZING DEAL!!! CLICK HERE!!!',  # Too much capitalization
            'aaaaaaaaaa',  # Repeated characters
        ]
        
        for comment in invalid_comments:
            with pytest.raises(ValidationError):
                validate_comment_content(comment)


class TestTagValidation:
    """Test tag name validation."""
    
    def test_valid_tag_names(self):
        """Test valid tag names."""
        valid_tags = [
            'python',
            'web-development',
            'machine_learning',
            'Django Framework',
        ]
        
        for tag in valid_tags:
            try:
                validate_tag_name(tag)
            except ValidationError:
                pytest.fail(f"Valid tag '{tag}' raised ValidationError")
    
    def test_invalid_tag_names(self):
        """Test invalid tag names."""
        invalid_tags = [
            '',  # Empty
            'a',  # Too short
            'x' * 51,  # Too long
            'tag@name',  # Invalid characters
            '   ',  # Only whitespace
        ]
        
        for tag in invalid_tags:
            with pytest.raises(ValidationError):
                validate_tag_name(tag)


class TestCategoryValidation:
    """Test category name validation."""
    
    def test_valid_category_names(self):
        """Test valid category names."""
        valid_categories = [
            'Technology',
            'Web Development',
            'Science & Research',
            'Business (General)',
        ]
        
        for category in valid_categories:
            try:
                validate_category_name(category)
            except ValidationError:
                pytest.fail(f"Valid category '{category}' raised ValidationError")
    
    def test_invalid_category_names(self):
        """Test invalid category names."""
        invalid_categories = [
            '',  # Empty
            'a',  # Too short
            'x' * 101,  # Too long
            'category#name',  # Invalid characters
            '   ',  # Only whitespace
        ]
        
        for category in invalid_categories:
            with pytest.raises(ValidationError):
                validate_category_name(category)