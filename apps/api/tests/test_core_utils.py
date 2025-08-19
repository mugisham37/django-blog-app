"""
Unit tests for core utilities.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from django.db import models
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from PIL import Image
from io import BytesIO

from apps.core.utils import (
    generate_unique_slug, process_uploaded_image, create_thumbnail,
    calculate_reading_time, extract_excerpt, send_notification_email,
    generate_cache_key, sanitize_filename, get_file_upload_path,
    truncate_words, is_valid_email, get_client_ip, format_file_size,
    clean_html_content, generate_random_string
)


# Mock model for testing
class MockModel(models.Model):
    slug = models.SlugField(max_length=50)
    
    class Meta:
        app_label = 'tests'
    
    @classmethod
    def objects_filter_exists_mock(cls, **kwargs):
        """Mock for objects.filter().exists()"""
        # Return False for most cases to simulate unique slug
        if kwargs.get('slug') == 'existing-slug':
            return True
        return False


class UtilsTestCase(TestCase):
    """Test cases for utility functions."""
    
    def test_generate_unique_slug_basic(self):
        """Test basic slug generation."""
        with patch.object(MockModel.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            slug = generate_unique_slug(MockModel, "Test Title")
            self.assertEqual(slug, "test-title")
    
    def test_generate_unique_slug_with_conflict(self):
        """Test slug generation with conflicts."""
        def mock_exists(slug_value):
            return slug_value in ['test-title', 'test-title-1']
        
        with patch.object(MockModel.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.side_effect = lambda: mock_exists(mock_filter.call_args[1]['slug'])
            
            # Mock the filter calls to simulate conflicts
            call_count = 0
            def mock_filter_func(**kwargs):
                nonlocal call_count
                call_count += 1
                mock_queryset = Mock()
                if call_count <= 2:  # First two calls return True (conflict)
                    mock_queryset.exists.return_value = True
                else:  # Third call returns False (no conflict)
                    mock_queryset.exists.return_value = False
                return mock_queryset
            
            mock_filter.side_effect = mock_filter_func
            
            slug = generate_unique_slug(MockModel, "Test Title")
            self.assertEqual(slug, "test-title-2")
    
    def test_generate_unique_slug_empty_title(self):
        """Test slug generation with empty title."""
        with patch.object(MockModel.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            slug = generate_unique_slug(MockModel, "")
            self.assertEqual(slug, "untitled")
    
    def test_generate_unique_slug_max_length(self):
        """Test slug generation with max length constraint."""
        with patch.object(MockModel.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            long_title = "This is a very long title that exceeds the maximum length"
            slug = generate_unique_slug(MockModel, long_title, max_length=20)
            
            self.assertLessEqual(len(slug), 20)
            self.assertTrue(slug.startswith("this-is-a-very-long"))
    
    def test_calculate_reading_time_basic(self):
        """Test basic reading time calculation."""
        content = "This is a test content with exactly ten words here."
        reading_time = calculate_reading_time(content, words_per_minute=10)
        self.assertEqual(reading_time, 1)  # 10 words at 10 wpm = 1 minute
    
    def test_calculate_reading_time_html_content(self):
        """Test reading time calculation with HTML content."""
        content = "<p>This is <strong>HTML</strong> content with <em>formatting</em>.</p>"
        reading_time = calculate_reading_time(content)
        self.assertGreater(reading_time, 0)
    
    def test_calculate_reading_time_empty_content(self):
        """Test reading time calculation with empty content."""
        reading_time = calculate_reading_time("")
        self.assertEqual(reading_time, 0)
    
    def test_extract_excerpt_basic(self):
        """Test basic excerpt extraction."""
        content = "This is a test content for excerpt extraction."
        excerpt = extract_excerpt(content, max_length=20)
        self.assertLessEqual(len(excerpt), 23)  # 20 + "..."
        self.assertTrue(excerpt.endswith("..."))
    
    def test_extract_excerpt_sentence_boundary(self):
        """Test excerpt extraction at sentence boundary."""
        content = "First sentence. Second sentence. Third sentence."
        excerpt = extract_excerpt(content, max_length=30, end_with_sentence=True)
        self.assertTrue(excerpt.endswith("First sentence.") or excerpt.endswith("..."))
    
    def test_extract_excerpt_html_content(self):
        """Test excerpt extraction from HTML content."""
        content = "<p>This is <strong>HTML</strong> content.</p>"
        excerpt = extract_excerpt(content)
        self.assertNotIn("<p>", excerpt)
        self.assertNotIn("<strong>", excerpt)
        self.assertIn("This is HTML content.", excerpt)
    
    def test_extract_excerpt_short_content(self):
        """Test excerpt extraction with content shorter than max_length."""
        content = "Short content."
        excerpt = extract_excerpt(content, max_length=100)
        self.assertEqual(excerpt, "Short content.")
    
    @patch('apps.core.utils.send_mail')
    @patch('apps.core.utils.render_to_string')
    def test_send_notification_email_success(self, mock_render, mock_send_mail):
        """Test successful email sending."""
        mock_render.return_value = "Test email content"
        mock_send_mail.return_value = True
        
        result = send_notification_email(
            'test@example.com',
            'Test Subject',
            'test_template',
            {'name': 'Test User'}
        )
        
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
    
    @patch('apps.core.utils.send_mail')
    def test_send_notification_email_failure(self, mock_send_mail):
        """Test email sending failure."""
        mock_send_mail.side_effect = Exception("SMTP Error")
        
        result = send_notification_email(
            'test@example.com',
            'Test Subject',
            'test_template',
            {'name': 'Test User'}
        )
        
        self.assertFalse(result)
    
    def test_generate_cache_key_basic(self):
        """Test basic cache key generation."""
        key = generate_cache_key('test', 'key')
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 32)  # MD5 hash length
    
    def test_generate_cache_key_with_objects(self):
        """Test cache key generation with objects."""
        mock_obj = Mock()
        mock_obj.id = 123
        mock_obj.__class__.__name__ = 'TestModel'
        
        key = generate_cache_key(mock_obj, test='value')
        self.assertIsInstance(key, str)
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        filename = sanitize_filename("test file.txt")
        self.assertEqual(filename, "test_file.txt")
    
    def test_sanitize_filename_special_chars(self):
        """Test filename sanitization with special characters."""
        filename = sanitize_filename("test@#$%file!.txt")
        self.assertEqual(filename, "test____file_.txt")
    
    def test_sanitize_filename_empty(self):
        """Test filename sanitization with empty input."""
        filename = sanitize_filename("")
        self.assertTrue(filename.startswith("file_"))
    
    def test_sanitize_filename_path_traversal(self):
        """Test filename sanitization prevents path traversal."""
        filename = sanitize_filename("../../../etc/passwd")
        self.assertEqual(filename, "passwd")
    
    def test_get_file_upload_path(self):
        """Test file upload path generation."""
        mock_instance = Mock()
        mock_instance.__class__.__name__ = 'TestModel'
        
        path = get_file_upload_path(mock_instance, "test.jpg")
        
        self.assertIn("uploads/testmodel/", path)
        self.assertTrue(path.endswith("test.jpg"))
        self.assertRegex(path, r'\d{4}/\d{2}/\d{2}')  # Date pattern
    
    def test_truncate_words_basic(self):
        """Test basic word truncation."""
        text = "This is a test sentence with many words."
        truncated = truncate_words(text, 5)
        self.assertEqual(truncated, "This is a test sentence...")
    
    def test_truncate_words_short_text(self):
        """Test word truncation with short text."""
        text = "Short text."
        truncated = truncate_words(text, 5)
        self.assertEqual(truncated, "Short text.")
    
    def test_truncate_words_empty_text(self):
        """Test word truncation with empty text."""
        truncated = truncate_words("", 5)
        self.assertEqual(truncated, "")
    
    def test_is_valid_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(is_valid_email(email))
    
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
            with self.subTest(email=email):
                self.assertFalse(is_valid_email(email))
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test client IP extraction with X-Forwarded-For header."""
        mock_request = Mock()
        mock_request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1'
        }
        
        ip = get_client_ip(mock_request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test client IP extraction without X-Forwarded-For header."""
        mock_request = Mock()
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        ip = get_client_ip(mock_request)
        self.assertEqual(ip, '127.0.0.1')
    
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        size = format_file_size(512)
        self.assertEqual(size, "512.0 B")
    
    def test_format_file_size_kb(self):
        """Test file size formatting for kilobytes."""
        size = format_file_size(1536)  # 1.5 KB
        self.assertEqual(size, "1.5 KB")
    
    def test_format_file_size_mb(self):
        """Test file size formatting for megabytes."""
        size = format_file_size(1572864)  # 1.5 MB
        self.assertEqual(size, "1.5 MB")
    
    def test_format_file_size_zero(self):
        """Test file size formatting for zero bytes."""
        size = format_file_size(0)
        self.assertEqual(size, "0 B")
    
    @patch('apps.core.utils.bleach')
    def test_clean_html_content_with_bleach(self, mock_bleach):
        """Test HTML content cleaning with bleach."""
        mock_bleach.clean.return_value = "Clean content"
        
        result = clean_html_content("<script>alert('xss')</script>Clean content")
        self.assertEqual(result, "Clean content")
        mock_bleach.clean.assert_called_once()
    
    def test_clean_html_content_without_bleach(self):
        """Test HTML content cleaning without bleach (fallback)."""
        with patch('apps.core.utils.bleach', side_effect=ImportError):
            content = "<p>Test content</p>"
            result = clean_html_content(content)
            self.assertEqual(result, content)  # Should return as-is
    
    def test_clean_html_content_empty(self):
        """Test HTML content cleaning with empty content."""
        result = clean_html_content("")
        self.assertEqual(result, "")
    
    def test_generate_random_string_default(self):
        """Test random string generation with defaults."""
        random_str = generate_random_string()
        self.assertEqual(len(random_str), 32)
        self.assertTrue(random_str.isalnum())
    
    def test_generate_random_string_custom_length(self):
        """Test random string generation with custom length."""
        random_str = generate_random_string(length=16)
        self.assertEqual(len(random_str), 16)
    
    def test_generate_random_string_lowercase_only(self):
        """Test random string generation with lowercase only."""
        random_str = generate_random_string(
            length=10,
            include_digits=False,
            include_uppercase=False
        )
        self.assertEqual(len(random_str), 10)
        self.assertTrue(random_str.islower())
        self.assertTrue(random_str.isalpha())


class ImageProcessingTestCase(TestCase):
    """Test cases for image processing utilities."""
    
    def create_test_image(self, width=800, height=600, format='JPEG'):
        """Create a test image for testing."""
        image = Image.new('RGB', (width, height), color='red')
        output = BytesIO()
        image.save(output, format=format)
        output.seek(0)
        return output
    
    def test_process_uploaded_image_basic(self):
        """Test basic image processing."""
        test_image = self.create_test_image()
        
        processed = process_uploaded_image(test_image)
        
        self.assertIsNotNone(processed)
        self.assertIsInstance(processed, ContentFile)
    
    def test_process_uploaded_image_resize(self):
        """Test image resizing during processing."""
        test_image = self.create_test_image(width=2000, height=1500)
        
        processed = process_uploaded_image(test_image, max_width=800, max_height=600)
        
        self.assertIsNotNone(processed)
        
        # Verify the image was resized
        processed.seek(0)
        resized_image = Image.open(processed)
        self.assertLessEqual(resized_image.width, 800)
        self.assertLessEqual(resized_image.height, 600)
    
    def test_process_uploaded_image_rgba_to_rgb(self):
        """Test RGBA to RGB conversion."""
        # Create RGBA image
        image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        output = BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        processed = process_uploaded_image(output, format='JPEG')
        
        self.assertIsNotNone(processed)
        
        # Verify conversion to RGB
        processed.seek(0)
        converted_image = Image.open(processed)
        self.assertEqual(converted_image.mode, 'RGB')
    
    def test_create_thumbnail_basic(self):
        """Test basic thumbnail creation."""
        test_image = self.create_test_image()
        
        thumbnail = create_thumbnail(test_image, size=(150, 150))
        
        self.assertIsNotNone(thumbnail)
        self.assertIsInstance(thumbnail, ContentFile)
        
        # Verify thumbnail size
        thumbnail.seek(0)
        thumb_image = Image.open(thumbnail)
        self.assertEqual(thumb_image.size, (150, 150))
    
    def test_create_thumbnail_no_crop(self):
        """Test thumbnail creation without cropping."""
        test_image = self.create_test_image(width=800, height=400)
        
        thumbnail = create_thumbnail(test_image, size=(200, 200), crop=False)
        
        self.assertIsNotNone(thumbnail)
        
        # Verify aspect ratio is maintained
        thumbnail.seek(0)
        thumb_image = Image.open(thumbnail)
        self.assertLessEqual(thumb_image.width, 200)
        self.assertLessEqual(thumb_image.height, 200)
        # Should maintain 2:1 aspect ratio
        self.assertAlmostEqual(thumb_image.width / thumb_image.height, 2.0, places=1)
    
    def test_process_uploaded_image_invalid_file(self):
        """Test image processing with invalid file."""
        invalid_file = BytesIO(b"Not an image")
        
        processed = process_uploaded_image(invalid_file)
        
        self.assertIsNone(processed)
    
    def test_create_thumbnail_invalid_file(self):
        """Test thumbnail creation with invalid file."""
        invalid_file = BytesIO(b"Not an image")
        
        thumbnail = create_thumbnail(invalid_file)
        
        self.assertIsNone(thumbnail)