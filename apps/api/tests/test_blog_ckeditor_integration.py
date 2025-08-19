"""
Tests for CKEditor integration and content processing in blog app.
Tests rich text editing, content sanitization, and preview functionality.
"""

import json
import tempfile
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch, MagicMock

from apps.blog.models import Post, Category, Tag
from apps.blog.forms import PostForm, PostPreviewForm
from apps.core.utils import clean_html_content, calculate_reading_time, extract_excerpt

User = get_user_model()


class CKEditorIntegrationTestCase(TestCase):
    """
    Test CKEditor integration and rich text editing functionality.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        self.tag = Tag.objects.create(
            name='Test Tag',
            slug='test-tag'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_post_form_ckeditor_widget(self):
        """
        Test that PostForm uses CKEditor widget for content field.
        """
        form = PostForm()
        
        # Check that content field uses CKEditorUploadingWidget
        self.assertIn('ckeditor', str(type(form.fields['content'].widget)))
        
        # Check widget configuration
        widget = form.fields['content'].widget
        self.assertEqual(widget.config_name, 'default')
    
    def test_content_sanitization(self):
        """
        Test HTML content sanitization for security.
        """
        # Test malicious content
        malicious_content = '''
        <p>Safe content</p>
        <script>alert('xss')</script>
        <iframe src="javascript:alert('xss')"></iframe>
        <img src="x" onerror="alert('xss')">
        <a href="javascript:alert('xss')">Link</a>
        '''
        
        cleaned_content = clean_html_content(malicious_content)
        
        # Check that dangerous elements are removed
        self.assertNotIn('<script>', cleaned_content)
        self.assertNotIn('<iframe>', cleaned_content)
        self.assertNotIn('onerror', cleaned_content)
        self.assertNotIn('javascript:', cleaned_content)
        
        # Check that safe content is preserved
        self.assertIn('<p>Safe content</p>', cleaned_content)
    
    def test_content_validation_ajax(self):
        """
        Test AJAX content validation endpoint.
        """
        content = '''
        <h2>Test Heading</h2>
        <p>This is a test paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
        <p>Another paragraph to test reading time calculation.</p>
        '''
        
        response = self.client.post(
            reverse('blog:validate_content'),
            data=json.dumps({
                'content': content,
                'title': 'Test Post',
                'excerpt': ''
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('cleaned_content', data)
        self.assertIn('reading_time', data)
        self.assertIn('excerpt', data)
        self.assertIn('word_count', data)
        
        # Check that reading time is calculated
        self.assertGreater(data['reading_time'], 0)
        
        # Check that word count is calculated
        self.assertGreater(data['word_count'], 0)
        
        # Check that excerpt is generated
        self.assertNotEqual(data['excerpt'], '')
    
    def test_reading_time_calculation(self):
        """
        Test reading time calculation for different content lengths.
        """
        # Short content (should be 1 minute minimum)
        short_content = "Short content."
        reading_time = calculate_reading_time(short_content)
        self.assertEqual(reading_time, 1)
        
        # Medium content
        medium_content = " ".join(["word"] * 100)  # 100 words
        reading_time = calculate_reading_time(medium_content)
        self.assertEqual(reading_time, 1)  # 100 words / 200 wpm = 0.5, rounded up to 1
        
        # Long content
        long_content = " ".join(["word"] * 400)  # 400 words
        reading_time = calculate_reading_time(long_content)
        self.assertEqual(reading_time, 2)  # 400 words / 200 wpm = 2
        
        # HTML content (tags should be stripped)
        html_content = "<p>" + " ".join(["word"] * 200) + "</p>"
        reading_time = calculate_reading_time(html_content)
        self.assertEqual(reading_time, 1)  # 200 words / 200 wpm = 1
    
    def test_excerpt_extraction(self):
        """
        Test automatic excerpt extraction from content.
        """
        # Test with HTML content
        html_content = '''
        <h2>Test Heading</h2>
        <p>This is the first paragraph that should be used for the excerpt. 
        It contains enough text to test the extraction functionality.</p>
        <p>This is the second paragraph that should not be included in the excerpt 
        if the first paragraph is long enough.</p>
        '''
        
        excerpt = extract_excerpt(html_content, max_length=100)
        
        # Check that HTML tags are stripped
        self.assertNotIn('<h2>', excerpt)
        self.assertNotIn('<p>', excerpt)
        
        # Check that content is truncated
        self.assertLessEqual(len(excerpt), 103)  # 100 + "..."
        
        # Check that it ends with sentence boundary or ellipsis
        self.assertTrue(excerpt.endswith('.') or excerpt.endswith('...'))
    
    def test_slug_generation_ajax(self):
        """
        Test AJAX slug generation endpoint.
        """
        response = self.client.post(
            reverse('blog:generate_slug'),
            data=json.dumps({
                'title': 'Test Post Title with Special Characters!@#'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('slug', data)
        
        # Check that slug is URL-friendly
        slug = data['slug']
        self.assertEqual(slug, 'test-post-title-with-special-characters')
    
    def test_slug_uniqueness(self):
        """
        Test that generated slugs are unique.
        """
        # Create a post with a specific slug
        Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            status=Post.Status.PUBLISHED
        )
        
        # Try to generate slug for same title
        response = self.client.post(
            reverse('blog:generate_slug'),
            data=json.dumps({
                'title': 'Test Post'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that slug is different (should have suffix)
        slug = data['slug']
        self.assertNotEqual(slug, 'test-post')
        self.assertTrue(slug.startswith('test-post-'))
    
    def create_test_image(self):
        """
        Create a test image for upload tests.
        """
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_file.getvalue(),
            content_type='image/jpeg'
        )
    
    @patch('apps.core.utils.process_uploaded_image')
    @patch('django.core.files.storage.default_storage.save')
    @patch('django.core.files.storage.default_storage.url')
    def test_ckeditor_image_upload(self, mock_url, mock_save, mock_process):
        """
        Test CKEditor image upload functionality.
        """
        # Mock the image processing and storage
        mock_process.return_value = MagicMock()
        mock_save.return_value = 'ckeditor/test_image.jpg'
        mock_url.return_value = '/media/ckeditor/test_image.jpg'
        
        test_image = self.create_test_image()
        
        response = self.client.post(
            reverse('blog:ckeditor_upload'),
            data={'upload': test_image},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('url', data)
        self.assertEqual(data['url'], '/media/ckeditor/test_image.jpg')
        
        # Check that image processing was called
        mock_process.assert_called_once()
        mock_save.assert_called_once()
    
    def test_ckeditor_upload_invalid_file(self):
        """
        Test CKEditor upload with invalid file type.
        """
        # Create a text file instead of image
        text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post(
            reverse('blog:ckeditor_upload'),
            data={'upload': text_file},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Only image files are allowed', data['error']['message'])
    
    def test_post_form_content_processing(self):
        """
        Test that PostForm properly processes content on save.
        """
        form_data = {
            'title': 'Test Post with Rich Content',
            'content': '''
            <h2>Test Heading</h2>
            <p>This is a test paragraph with <strong>bold</strong> text.</p>
            <script>alert('xss')</script>
            <p>Another paragraph for testing.</p>
            ''',
            'status': Post.Status.DRAFT,
            'category': self.category.id,
            'tags': [self.tag.id],
            'allow_comments': True
        }
        
        form = PostForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        post = form.save()
        
        # Check that content was sanitized
        self.assertNotIn('<script>', post.content)
        self.assertIn('<h2>Test Heading</h2>', post.content)
        self.assertIn('<strong>bold</strong>', post.content)
        
        # Check that reading time was calculated
        self.assertGreater(post.reading_time, 0)
        
        # Check that excerpt was generated
        self.assertNotEqual(post.excerpt, '')
        self.assertIn('Test Heading', post.excerpt)


class PostPreviewTestCase(TestCase):
    """
    Test post preview functionality.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='<p>Test content for preview</p>',
            author=self.user,
            category=self.category,
            status=Post.Status.DRAFT
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_post_preview_view_existing_post(self):
        """
        Test preview view for existing post.
        """
        response = self.client.get(
            reverse('blog:post_preview', kwargs={'pk': self.post.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test content for preview')
        self.assertContains(response, 'Preview Mode')
    
    def test_post_preview_ajax(self):
        """
        Test AJAX post preview functionality.
        """
        preview_data = {
            'title': 'Preview Test Post',
            'content': '<h2>Preview Heading</h2><p>Preview content with <strong>formatting</strong>.</p>',
            'excerpt': 'This is a preview excerpt.',
            'category': self.category.id
        }
        
        response = self.client.post(
            reverse('blog:post_preview_ajax'),
            data=json.dumps(preview_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('html', data)
        self.assertIn('reading_time', data)
        
        # Check that preview HTML contains expected content
        html = data['html']
        self.assertIn('Preview Test Post', html)
        self.assertIn('Preview Heading', html)
        self.assertIn('<strong>formatting</strong>', html)
        
        # Check that reading time is calculated
        self.assertGreater(data['reading_time'], 0)
    
    def test_preview_form_widget_configuration(self):
        """
        Test that PostPreviewForm has correct widget configuration.
        """
        form = PostPreviewForm()
        
        # Check that content field uses CKEditor widget
        self.assertIn('ckeditor', str(type(form.fields['content'].widget)))
        
        # Check that other fields are read-only
        for field_name, field in form.fields.items():
            if field_name != 'content':
                widget_attrs = field.widget.attrs
                self.assertTrue(
                    widget_attrs.get('readonly') or widget_attrs.get('disabled'),
                    f"Field {field_name} should be read-only in preview form"
                )
    
    def test_preview_unauthorized_access(self):
        """
        Test that preview requires authentication.
        """
        self.client.logout()
        
        response = self.client.get(
            reverse('blog:post_preview', kwargs={'pk': self.post.pk})
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_preview_other_user_post(self):
        """
        Test that users can only preview their own posts.
        """
        # Create another user and post
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        other_post = Post.objects.create(
            title='Other User Post',
            slug='other-user-post',
            content='<p>Other user content</p>',
            author=other_user,
            status=Post.Status.DRAFT
        )
        
        # Try to preview other user's post
        response = self.client.get(
            reverse('blog:post_preview', kwargs={'pk': other_post.pk})
        )
        
        self.assertEqual(response.status_code, 404)


class CKEditorConfigurationTestCase(TestCase):
    """
    Test CKEditor configuration and settings.
    """
    
    def test_ckeditor_settings_exist(self):
        """
        Test that CKEditor settings are properly configured.
        """
        # Check that CKEditor is in INSTALLED_APPS
        self.assertIn('ckeditor', settings.INSTALLED_APPS)
        self.assertIn('ckeditor_uploader', settings.INSTALLED_APPS)
        
        # Check CKEditor configuration
        self.assertTrue(hasattr(settings, 'CKEDITOR_CONFIGS'))
        self.assertIn('default', settings.CKEDITOR_CONFIGS)
        
        # Check default configuration
        default_config = settings.CKEDITOR_CONFIGS['default']
        self.assertIn('toolbar', default_config)
        self.assertIn('height', default_config)
        self.assertIn('extraPlugins', default_config)
        
        # Check upload settings
        self.assertTrue(hasattr(settings, 'CKEDITOR_UPLOAD_PATH'))
        self.assertTrue(hasattr(settings, 'CKEDITOR_IMAGE_BACKEND'))
    
    def test_ckeditor_security_settings(self):
        """
        Test CKEditor security-related settings.
        """
        default_config = settings.CKEDITOR_CONFIGS['default']
        
        # Check that allowedContent is configured
        self.assertIn('allowedContent', default_config)
        
        # Check that dangerous plugins are removed
        removed_plugins = default_config.get('removePlugins', '')
        self.assertIn('stylesheetparser', removed_plugins)
        
        # Check upload restrictions
        self.assertFalse(settings.CKEDITOR_ALLOW_NONIMAGE_FILES)
        self.assertTrue(settings.CKEDITOR_UPLOAD_SLUGIFY_FILENAME)
    
    def test_multiple_ckeditor_configs(self):
        """
        Test that multiple CKEditor configurations exist for different use cases.
        """
        configs = settings.CKEDITOR_CONFIGS
        
        # Check that different configs exist
        self.assertIn('default', configs)
        self.assertIn('admin', configs)
        self.assertIn('comment', configs)
        
        # Check that admin config is more restrictive
        admin_config = configs['admin']
        default_config = configs['default']
        
        self.assertLess(admin_config['height'], default_config['height'])
        self.assertLess(len(admin_config['toolbar_Custom']), len(default_config['toolbar_Custom']))
        
        # Check that comment config is most restrictive
        comment_config = configs['comment']
        self.assertIn('forcePasteAsPlainText', comment_config)
        self.assertTrue(comment_config['forcePasteAsPlainText'])