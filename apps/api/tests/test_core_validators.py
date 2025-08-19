"""
Tests for core validators in Django Personal Blog System.
"""

import os
import tempfile
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from PIL import Image
import io

from apps.core.validators import (
    validate_slug_format,
    validate_content_length,
    validate_html_content,
    validate_image_file,
    validate_email_domain,
    validate_password_strength,
    validate_url_safety,
    validate_username_format,
    validate_comment_content,
    validate_tag_name,
    validate_category_name,
    validate_file_upload
)


class ValidateSlugFormatTestCase(TestCase):
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
            with self.subTest(slug=slug):
                try:
                    validate_slug_format(slug)
                except ValidationError:
                    self.fail(f"Valid slug '{slug}' raised ValidationError")
    
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
            with self.subTest(slug=slug):
                with self.assertRaises(ValidationError):
                    validate_slug_format(slug)
    
    def test_reserved_words(self):
        """Test reserved word validation."""
        reserved_words = ['admin', 'api', 'blog', 'login']
        
        for word in reserved_words:
            with self.subTest(word=word):
                with self.assertRaises(ValidationError):
                    validate_slug_format(word)


class ValidateContentLengthTestCase(TestCase):
    """Test content length validation."""
    
    def test_valid_content_length(self):
        """Test valid content lengths."""
        valid_content = "This is a valid content with sufficient length."
        
        try:
            validate_content_length(valid_content)
        except ValidationError:
            self.fail("Valid content raised ValidationError")
    
    def test_content_too_short(self):
        """Test content that is too short."""
        short_content = "Short"
        
        with self.assertRaises(ValidationError):
            validate_content_length(short_content)
    
    def test_content_too_long(self):
        """Test content that is too long."""
        long_content = "x" * 60000
        
        with self.assertRaises(ValidationError):
            validate_content_length(long_content)
    
    def test_html_content_length(self):
        """Test content length calculation with HTML tags."""
        html_content = "<p>This is a valid content with sufficient length.</p>"
        
        try:
            validate_content_length(html_content)
        except ValidationError:
            self.fail("Valid HTML content raised ValidationError")
    
    def test_empty_content(self):
        """Test empty content validation."""
        with self.assertRaises(ValidationError):
            validate_content_length("")
        
        with self.assertRaises(ValidationError):
            validate_content_length(None)


class ValidateHtmlContentTestCase(TestCase):
    """Test HTML content validation."""
    
    def test_safe_html_content(self):
        """Test safe HTML content."""
        safe_html = "<p>This is <strong>safe</strong> HTML content.</p>"
        
        try:
            validate_html_content(safe_html)
        except ValidationError:
            self.fail("Safe HTML content raised ValidationError")
    
    def test_dangerous_tags(self):
        """Test dangerous HTML tags."""
        dangerous_html_samples = [
            "<script>alert('xss')</script>",
            "<iframe src='malicious.com'></iframe>",
            "<form><input type='text'></form>",
            "<object data='malicious.swf'></object>",
        ]
        
        for html in dangerous_html_samples:
            with self.subTest(html=html):
                with self.assertRaises(ValidationError):
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
            with self.subTest(html=html):
                with self.assertRaises(ValidationError):
                    validate_html_content(html)
    
    def test_empty_html_content(self):
        """Test empty HTML content."""
        try:
            validate_html_content("")
            validate_html_content(None)
        except ValidationError:
            self.fail("Empty HTML content should not raise ValidationError")


class ValidateImageFileTestCase(TestCase):
    """Test image file validation."""
    
    def setUp(self):
        """Set up test image files."""
        # Create a valid test image
        self.valid_image = self._create_test_image('RGB', (200, 200))
        self.large_image = self._create_test_image('RGB', (5000, 5000))
        self.small_image = self._create_test_image('RGB', (50, 50))
    
    def _create_test_image(self, mode, size):
        """Create a test image file."""
        image = Image.new(mode, size, color='red')
        image_file = io.BytesIO()
        image.save(image_file, format='PNG')
        image_file.seek(0)
        
        return SimpleUploadedFile(
            name='test.png',
            content=image_file.getvalue(),
            content_type='image/png'
        )
    
    def test_valid_image(self):
        """Test valid image file."""
        try:
            validate_image_file(self.valid_image)
        except ValidationError:
            self.fail("Valid image raised ValidationError")
    
    @override_settings(MAX_IMAGE_SIZE=1024*1024)  # 1MB
    def test_image_too_large(self):
        """Test image file that is too large."""
        with self.assertRaises(ValidationError):
            validate_image_file(self.large_image)
    
    @override_settings(MIN_IMAGE_WIDTH=100, MIN_IMAGE_HEIGHT=100)
    def test_image_too_small(self):
        """Test image dimensions that are too small."""
        with self.assertRaises(ValidationError):
            validate_image_file(self.small_image)
    
    def test_invalid_file_extension(self):
        """Test invalid file extension."""
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        with self.assertRaises(ValidationError):
            validate_image_file(invalid_file)
    
    def test_empty_image_file(self):
        """Test empty image file."""
        try:
            validate_image_file(None)
        except ValidationError:
            self.fail("Empty image file should not raise ValidationError")


class ValidateEmailDomainTestCase(TestCase):
    """Test email domain validation."""
    
    def test_valid_email_domains(self):
        """Test valid email domains."""
        valid_emails = [
            'user@example.com',
            'test@gmail.com',
            'admin@company.org',
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                try:
                    validate_email_domain(email)
                except ValidationError:
                    self.fail(f"Valid email '{email}' raised ValidationError")
    
    @override_settings(BLACKLISTED_EMAIL_DOMAINS=['tempmail.org', 'spam.com'])
    def test_blacklisted_domains(self):
        """Test blacklisted email domains."""
        blacklisted_emails = [
            'user@tempmail.org',
            'test@spam.com',
        ]
        
        for email in blacklisted_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    validate_email_domain(email)
    
    @override_settings(REQUIRED_EMAIL_DOMAINS=['company.com'])
    def test_required_domains(self):
        """Test required email domains."""
        # Valid domain
        try:
            validate_email_domain('user@company.com')
        except ValidationError:
            self.fail("Email from required domain raised ValidationError")
        
        # Invalid domain
        with self.assertRaises(ValidationError):
            validate_email_domain('user@gmail.com')
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        invalid_emails = [
            'invalid-email',
            'user@',
            '@domain.com',
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    validate_email_domain(email)


class ValidatePasswordStrengthTestCase(TestCase):
    """Test password strength validation."""
    
    def test_strong_password(self):
        """Test strong password."""
        strong_password = "StrongP@ssw0rd123"
        
        try:
            validate_password_strength(strong_password)
        except ValidationError:
            self.fail("Strong password raised ValidationError")
    
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
            with self.subTest(password=password):
                with self.assertRaises(ValidationError):
                    validate_password_strength(password)
    
    def test_empty_password(self):
        """Test empty password."""
        try:
            validate_password_strength("")
            validate_password_strength(None)
        except ValidationError:
            self.fail("Empty password should not raise ValidationError")


class ValidateUrlSafetyTestCase(TestCase):
    """Test URL safety validation."""
    
    def test_safe_urls(self):
        """Test safe URLs."""
        safe_urls = [
            'https://example.com',
            'http://blog.example.org/post/123',
            'https://subdomain.example.com/path?param=value',
        ]
        
        for url in safe_urls:
            with self.subTest(url=url):
                try:
                    validate_url_safety(url)
                except ValidationError:
                    self.fail(f"Safe URL '{url}' raised ValidationError")
    
    def test_dangerous_protocols(self):
        """Test dangerous URL protocols."""
        dangerous_urls = [
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            'vbscript:msgbox(1)',
            'file:///etc/passwd',
        ]
        
        for url in dangerous_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    validate_url_safety(url)
    
    def test_suspicious_content(self):
        """Test URLs with suspicious content."""
        suspicious_urls = [
            'https://example.com/<script>alert(1)</script>',
            'https://example.com/?param=javascript:alert(1)',
            'https://example.com/eval(malicious)',
        ]
        
        for url in suspicious_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    validate_url_safety(url)
    
    def test_invalid_url_format(self):
        """Test invalid URL format."""
        invalid_urls = [
            'not-a-url',
            'http://',
            'https://.',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    validate_url_safety(url)


class ValidateUsernameFormatTestCase(TestCase):
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
            with self.subTest(username=username):
                try:
                    validate_username_format(username)
                except ValidationError:
                    self.fail(f"Valid username '{username}' raised ValidationError")
    
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
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    validate_username_format(username)
    
    def test_reserved_usernames(self):
        """Test reserved username validation."""
        reserved_usernames = ['admin', 'root', 'system', 'api']
        
        for username in reserved_usernames:
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    validate_username_format(username)


class ValidateCommentContentTestCase(TestCase):
    """Test comment content validation."""
    
    def test_valid_comment(self):
        """Test valid comment content."""
        valid_comment = "This is a valid comment with sufficient content."
        
        try:
            validate_comment_content(valid_comment)
        except ValidationError:
            self.fail("Valid comment raised ValidationError")
    
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
            with self.subTest(comment=comment):
                with self.assertRaises(ValidationError):
                    validate_comment_content(comment)
    
    def test_spam_detection(self):
        """Test spam pattern detection in comments."""
        # These should not raise ValidationError but should be logged
        spam_comments = [
            'Click here for amazing deals!',
            'Make money from home easily!',
            'Buy now, limited time offer!',
        ]
        
        for comment in spam_comments:
            with self.subTest(comment=comment):
                try:
                    validate_comment_content(comment)
                except ValidationError:
                    self.fail(f"Spam comment '{comment}' should not raise ValidationError")


class ValidateTagNameTestCase(TestCase):
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
            with self.subTest(tag=tag):
                try:
                    validate_tag_name(tag)
                except ValidationError:
                    self.fail(f"Valid tag '{tag}' raised ValidationError")
    
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
            with self.subTest(tag=tag):
                with self.assertRaises(ValidationError):
                    validate_tag_name(tag)


class ValidateCategoryNameTestCase(TestCase):
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
            with self.subTest(category=category):
                try:
                    validate_category_name(category)
                except ValidationError:
                    self.fail(f"Valid category '{category}' raised ValidationError")
    
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
            with self.subTest(category=category):
                with self.assertRaises(ValidationError):
                    validate_category_name(category)


class ValidateFileUploadTestCase(TestCase):
    """Test general file upload validation."""
    
    def test_valid_file_upload(self):
        """Test valid file upload."""
        valid_file = SimpleUploadedFile(
            name='document.pdf',
            content=b'PDF content here',
            content_type='application/pdf'
        )
        
        try:
            validate_file_upload(valid_file)
        except ValidationError:
            self.fail("Valid file upload raised ValidationError")
    
    def test_invalid_file_extension(self):
        """Test invalid file extension."""
        invalid_file = SimpleUploadedFile(
            name='malicious.exe',
            content=b'Executable content',
            content_type='application/octet-stream'
        )
        
        with self.assertRaises(ValidationError):
            validate_file_upload(invalid_file)
    
    def test_dangerous_filename(self):
        """Test dangerous filename."""
        dangerous_file = SimpleUploadedFile(
            name='index.html',
            content=b'<html>content</html>',
            content_type='text/html'
        )
        
        with self.assertRaises(ValidationError):
            validate_file_upload(dangerous_file)
    
    def test_empty_file_upload(self):
        """Test empty file upload."""
        try:
            validate_file_upload(None)
        except ValidationError:
            self.fail("Empty file upload should not raise ValidationError")