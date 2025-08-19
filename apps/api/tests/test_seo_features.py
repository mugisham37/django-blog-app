"""
Tests for SEO optimization features in Django Personal Blog System.
Tests slug generation, meta tag generation, Open Graph images, and reading time calculation.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

from apps.blog.models import Post, Category, Tag
from apps.core.utils import (
    generate_slug_with_validation, generate_meta_title, generate_meta_description,
    extract_keywords_from_content, create_open_graph_image, calculate_enhanced_reading_time,
    validate_seo_content
)

User = get_user_model()


class SEOUtilsTestCase(TestCase):
    """Test SEO utility functions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
    
    def test_generate_slug_with_validation(self):
        """Test enhanced slug generation with validation."""
        # Test basic slug generation
        slug = generate_slug_with_validation(Post, 'My Test Post')
        self.assertEqual(slug, 'my-test-post')
        
        # Test slug uniqueness
        Post.objects.create(
            title='Test Post',
            slug='my-test-post',
            content='Test content',
            author=self.user
        )
        
        slug = generate_slug_with_validation(Post, 'My Test Post')
        self.assertEqual(slug, 'my-test-post-1')
        
        # Test reserved slug handling
        slug = generate_slug_with_validation(Post, 'admin')
        self.assertEqual(slug, 'post-admin')
        
        # Test empty title handling
        slug = generate_slug_with_validation(Post, '')
        self.assertEqual(slug, 'untitled')
        
        # Test special characters removal
        slug = generate_slug_with_validation(Post, 'Test!@#$%^&*()Post')
        self.assertEqual(slug, 'testpost')
        
        # Test max length handling
        long_title = 'a' * 250
        slug = generate_slug_with_validation(Post, long_title, max_length=50)
        self.assertLessEqual(len(slug), 50)
    
    def test_generate_meta_title(self):
        """Test meta title generation."""
        # Test basic meta title
        meta_title = generate_meta_title('My Blog Post')
        self.assertEqual(meta_title, 'My Blog Post')
        
        # Test with site name
        meta_title = generate_meta_title('My Blog Post', site_name='My Blog')
        self.assertEqual(meta_title, 'My Blog Post | My Blog')
        
        # Test length truncation
        long_title = 'This is a very long title that should be truncated'
        meta_title = generate_meta_title(long_title, site_name='My Blog', max_length=60)
        self.assertLessEqual(len(meta_title), 60)
        self.assertIn('My Blog', meta_title)
        
        # Test empty title with site name
        meta_title = generate_meta_title('', site_name='My Blog')
        self.assertEqual(meta_title, 'My Blog')
    
    def test_generate_meta_description(self):
        """Test meta description generation."""
        content = '<p>This is a test blog post with some <strong>HTML</strong> content. ' \
                 'It should be converted to a proper meta description.</p>'
        
        # Test basic description generation
        description = generate_meta_description(content)
        self.assertNotIn('<p>', description)
        self.assertNotIn('<strong>', description)
        self.assertIn('This is a test blog post', description)
        
        # Test with existing excerpt
        excerpt = 'This is a custom excerpt'
        description = generate_meta_description(content, excerpt=excerpt)
        self.assertEqual(description, excerpt)
        
        # Test length truncation
        long_content = '<p>' + 'word ' * 100 + '</p>'
        description = generate_meta_description(long_content, max_length=160)
        self.assertLessEqual(len(description), 160)
        
        # Test empty content
        description = generate_meta_description('')
        self.assertEqual(description, '')
    
    def test_extract_keywords_from_content(self):
        """Test keyword extraction from content."""
        content = '''
        <p>This is a blog post about Django and Python programming.
        Django is a web framework for Python developers. Python is a
        programming language that is popular for web development.</p>
        '''
        
        keywords = extract_keywords_from_content(content, max_keywords=5)
        
        # Should extract meaningful keywords
        self.assertIn('django', keywords)
        self.assertIn('python', keywords)
        self.assertIn('programming', keywords)
        
        # Should not include stop words
        self.assertNotIn('the', keywords)
        self.assertNotIn('and', keywords)
        self.assertNotIn('for', keywords)
        
        # Should respect max_keywords limit
        self.assertLessEqual(len(keywords), 5)
        
        # Test empty content
        keywords = extract_keywords_from_content('')
        self.assertEqual(keywords, [])
    
    @patch('apps.core.utils.Image')
    @patch('apps.core.utils.ImageDraw')
    @patch('apps.core.utils.ImageFont')
    def test_create_open_graph_image(self, mock_font, mock_draw, mock_image):
        """Test Open Graph image generation."""
        # Mock PIL objects
        mock_img = MagicMock()
        mock_image.new.return_value = mock_img
        mock_draw_obj = MagicMock()
        mock_draw.Draw.return_value = mock_draw_obj
        mock_font.truetype.return_value = MagicMock()
        
        # Mock save method to return BytesIO content
        def mock_save(output, **kwargs):
            output.write(b'fake_image_data')
        mock_img.save.side_effect = mock_save
        
        # Test image generation
        result = create_open_graph_image('Test Title', 'Test Subtitle')
        
        # Should return ContentFile
        self.assertIsInstance(result, ContentFile)
        
        # Should call PIL methods
        mock_image.new.assert_called_once()
        mock_draw.Draw.assert_called_once()
        mock_img.save.assert_called_once()
    
    def test_calculate_enhanced_reading_time(self):
        """Test enhanced reading time calculation."""
        # Test basic calculation
        content = 'word ' * 200  # 200 words
        reading_time = calculate_enhanced_reading_time(content, words_per_minute=200)
        self.assertEqual(reading_time, 1)  # Should be 1 minute
        
        # Test with HTML content
        html_content = '<p>' + 'word ' * 400 + '</p>'  # 400 words
        reading_time = calculate_enhanced_reading_time(html_content, words_per_minute=200)
        self.assertEqual(reading_time, 2)  # Should be 2 minutes
        
        # Test with images
        content_with_images = 'word ' * 100 + '<img src="test.jpg">' * 5
        reading_time = calculate_enhanced_reading_time(content_with_images, include_images=True)
        self.assertGreater(reading_time, 1)  # Should be more than just word count
        
        # Test minimum reading time
        short_content = 'short'
        reading_time = calculate_enhanced_reading_time(short_content)
        self.assertEqual(reading_time, 1)  # Should be at least 1 minute
        
        # Test empty content
        reading_time = calculate_enhanced_reading_time('')
        self.assertEqual(reading_time, 0)
    
    def test_validate_seo_content(self):
        """Test SEO content validation."""
        # Test valid content
        result = validate_seo_content(
            title='Great Blog Post Title',
            content='<p>' + 'word ' * 300 + '</p>',
            meta_title='Great Blog Post Title | My Blog',
            meta_description='This is a great blog post about testing SEO features in Django applications.'
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('overall', result['scores'])
        self.assertGreater(result['scores']['overall'], 50)
        
        # Test invalid content
        result = validate_seo_content(
            title='',  # Empty title
            content='Short content',  # Too short
            meta_title='This is a very long meta title that exceeds the recommended length',
            meta_description=''  # Empty description
        )
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertGreater(len(result['suggestions']), 0)


class PostSEOTestCase(TestCase):
    """Test SEO features in Post model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        self.tag1 = Tag.objects.create(name='Django', slug='django')
        self.tag2 = Tag.objects.create(name='Python', slug='python')
    
    def test_post_slug_generation(self):
        """Test automatic slug generation for posts."""
        post = Post.objects.create(
            title='My Amazing Blog Post',
            content='<p>This is test content</p>',
            author=self.user,
            category=self.category
        )
        
        self.assertEqual(post.slug, 'my-amazing-blog-post')
        
        # Test slug uniqueness
        post2 = Post.objects.create(
            title='My Amazing Blog Post',  # Same title
            content='<p>Different content</p>',
            author=self.user,
            category=self.category
        )
        
        self.assertEqual(post2.slug, 'my-amazing-blog-post-1')
    
    def test_post_seo_fields_auto_generation(self):
        """Test automatic generation of SEO fields."""
        with self.settings(SITE_NAME='Test Blog'):
            post = Post.objects.create(
                title='Test Post',
                content='<p>' + 'word ' * 100 + '</p>',
                author=self.user,
                category=self.category
            )
            
            # Should auto-generate meta_title
            self.assertIn('Test Post', post.meta_title)
            self.assertIn('Test Blog', post.meta_title)
            
            # Should auto-generate meta_description
            self.assertTrue(post.meta_description)
            self.assertLessEqual(len(post.meta_description), 160)
            
            # Should calculate reading time
            self.assertGreater(post.reading_time, 0)
    
    def test_post_seo_methods(self):
        """Test SEO-related methods in Post model."""
        post = Post.objects.create(
            title='Test Post',
            content='<p>This is a test post about Django and Python programming.</p>',
            excerpt='Custom excerpt',
            meta_title='Custom Meta Title',
            meta_description='Custom meta description',
            author=self.user,
            category=self.category
        )
        post.tags.add(self.tag1, self.tag2)
        
        # Test get_seo_title
        self.assertEqual(post.get_seo_title(), 'Custom Meta Title')
        
        # Test get_seo_description
        self.assertEqual(post.get_seo_description(), 'Custom meta description')
        
        # Test get_keywords
        keywords = post.get_keywords()
        self.assertIn('Django', keywords)
        self.assertIn('Python', keywords)
        self.assertIn('Technology', keywords)
        
        # Test get_structured_data
        structured_data = post.get_structured_data()
        self.assertEqual(structured_data['@type'], 'BlogPosting')
        self.assertEqual(structured_data['headline'], 'Test Post')
        self.assertIn('keywords', structured_data)
        
        # Test validate_seo
        seo_validation = post.validate_seo()
        self.assertIn('scores', seo_validation)
        self.assertIn('overall', seo_validation['scores'])
    
    def test_post_reading_time_calculation(self):
        """Test reading time calculation for posts."""
        # Short content
        short_post = Post.objects.create(
            title='Short Post',
            content='<p>Short content</p>',
            author=self.user
        )
        self.assertEqual(short_post.reading_time, 1)  # Minimum 1 minute
        
        # Long content
        long_content = '<p>' + 'word ' * 1000 + '</p>'
        long_post = Post.objects.create(
            title='Long Post',
            content=long_content,
            author=self.user
        )
        self.assertGreater(long_post.reading_time, 1)
        
        # Test reading time display
        self.assertEqual(short_post.get_reading_time_display(), '1 minute read')
        self.assertIn('minutes read', long_post.get_reading_time_display())


class SEOTemplateTagsTestCase(TestCase):
    """Test SEO template tags."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='<p>Test content</p>',
            excerpt='Test excerpt',
            meta_title='Test Meta Title',
            meta_description='Test meta description',
            author=self.user,
            category=self.category
        )
    
    def test_meta_title_tag(self):
        """Test meta_title template tag."""
        template = Template('{% load seo_tags %}{% meta_title post %}')
        context = Context({'post': self.post})
        output = template.render(context)
        
        self.assertIn('<title>', output)
        self.assertIn('Test Meta Title', output)
    
    def test_meta_description_tag(self):
        """Test meta_description template tag."""
        template = Template('{% load seo_tags %}{% meta_description post %}')
        context = Context({'post': self.post})
        output = template.render(context)
        
        self.assertIn('name="description"', output)
        self.assertIn('Test meta description', output)
    
    def test_meta_keywords_tag(self):
        """Test meta_keywords template tag."""
        tag1 = Tag.objects.create(name='Django', slug='django')
        tag2 = Tag.objects.create(name='Python', slug='python')
        self.post.tags.add(tag1, tag2)
        
        template = Template('{% load seo_tags %}{% meta_keywords post %}')
        context = Context({'post': self.post})
        output = template.render(context)
        
        self.assertIn('name="keywords"', output)
        self.assertIn('Django', output)
        self.assertIn('Python', output)
    
    def test_og_tags(self):
        """Test Open Graph template tags."""
        request = self.factory.get('/test/')
        template = Template('{% load seo_tags %}{% og_tags post request %}')
        context = Context({'post': self.post, 'request': request})
        output = template.render(context)
        
        self.assertIn('property="og:title"', output)
        self.assertIn('property="og:description"', output)
        self.assertIn('property="og:type"', output)
        self.assertIn('content="article"', output)
    
    def test_twitter_card_tags(self):
        """Test Twitter Card template tags."""
        request = self.factory.get('/test/')
        template = Template('{% load seo_tags %}{% twitter_card_tags post request %}')
        context = Context({'post': self.post, 'request': request})
        output = template.render(context)
        
        self.assertIn('name="twitter:card"', output)
        self.assertIn('name="twitter:title"', output)
        self.assertIn('name="twitter:description"', output)
    
    def test_structured_data_tag(self):
        """Test structured data template tag."""
        template = Template('{% load seo_tags %}{% structured_data post %}')
        context = Context({'post': self.post})
        output = template.render(context)
        
        self.assertIn('application/ld+json', output)
        self.assertIn('BlogPosting', output)
        
        # Validate JSON structure
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        json_data = output[json_start:json_end]
        parsed_data = json.loads(json_data)
        
        self.assertEqual(parsed_data['@type'], 'BlogPosting')
        self.assertEqual(parsed_data['headline'], 'Test Post')
    
    def test_canonical_url_tag(self):
        """Test canonical URL template tag."""
        request = self.factory.get('/test/')
        template = Template('{% load seo_tags %}{% canonical_url post request %}')
        context = Context({'post': self.post, 'request': request})
        output = template.render(context)
        
        self.assertIn('rel="canonical"', output)
        self.assertIn('href=', output)
    
    def test_reading_time_tag(self):
        """Test reading time template tag."""
        template = Template('{% load seo_tags %}{% reading_time post %}')
        context = Context({'post': self.post})
        output = template.render(context)
        
        self.assertIn('minute', output)
        self.assertIn('read', output)
    
    def test_seo_score_class_filter(self):
        """Test SEO score class filter."""
        template = Template('{% load seo_tags %}{{ score|seo_score_class }}')
        
        # Test excellent score
        context = Context({'score': 85})
        output = template.render(context)
        self.assertEqual(output, 'seo-score-excellent')
        
        # Test good score
        context = Context({'score': 70})
        output = template.render(context)
        self.assertEqual(output, 'seo-score-good')
        
        # Test fair score
        context = Context({'score': 50})
        output = template.render(context)
        self.assertEqual(output, 'seo-score-fair')
        
        # Test poor score
        context = Context({'score': 30})
        output = template.render(context)
        self.assertEqual(output, 'seo-score-poor')
    
    def test_breadcrumb_structured_data(self):
        """Test breadcrumb structured data generation."""
        breadcrumbs = [
            {'name': 'Home', 'url': '/'},
            {'name': 'Blog', 'url': '/blog/'},
            {'name': 'Test Post', 'url': '/blog/test-post/'}
        ]
        
        template = Template('{% load seo_tags %}{% breadcrumb_structured_data breadcrumbs %}')
        context = Context({'breadcrumbs': breadcrumbs})
        output = template.render(context)
        
        self.assertIn('BreadcrumbList', output)
        self.assertIn('ListItem', output)
        
        # Validate JSON structure
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        json_data = output[json_start:json_end]
        parsed_data = json.loads(json_data)
        
        self.assertEqual(parsed_data['@type'], 'BreadcrumbList')
        self.assertEqual(len(parsed_data['itemListElement']), 3)
        self.assertEqual(parsed_data['itemListElement'][0]['name'], 'Home')


class SEOIntegrationTestCase(TestCase):
    """Integration tests for SEO features."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
    
    def test_complete_seo_workflow(self):
        """Test complete SEO workflow from post creation to template rendering."""
        # Create post with minimal data
        post = Post.objects.create(
            title='Complete SEO Test Post',
            content='<p>' + 'This is a comprehensive test of SEO features. ' * 50 + '</p>',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED
        )
        
        # Add tags
        tag1 = Tag.objects.create(name='SEO', slug='seo')
        tag2 = Tag.objects.create(name='Testing', slug='testing')
        post.tags.add(tag1, tag2)
        
        # Verify auto-generated SEO fields
        self.assertTrue(post.slug)
        self.assertTrue(post.meta_title)
        self.assertTrue(post.meta_description)
        self.assertGreater(post.reading_time, 0)
        
        # Test SEO methods
        keywords = post.get_keywords()
        self.assertIn('SEO', keywords)
        self.assertIn('Testing', keywords)
        self.assertIn('Technology', keywords)
        
        structured_data = post.get_structured_data()
        self.assertEqual(structured_data['@type'], 'BlogPosting')
        self.assertIn('keywords', structured_data)
        
        seo_validation = post.validate_seo()
        self.assertIn('scores', seo_validation)
        
        # Test template rendering
        from django.template import Template, Context, RequestContext
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/test/')
        
        template = Template('''
            {% load seo_tags %}
            {% meta_title post %}
            {% meta_description post %}
            {% og_tags post request %}
            {% structured_data post %}
        ''')
        
        context = Context({'post': post, 'request': request})
        output = template.render(context)
        
        # Verify all SEO elements are present
        self.assertIn('<title>', output)
        self.assertIn('name="description"', output)
        self.assertIn('property="og:', output)
        self.assertIn('application/ld+json', output)
        self.assertIn('BlogPosting', output)
    
    def test_seo_performance_with_large_dataset(self):
        """Test SEO features performance with larger dataset."""
        # Create multiple posts
        posts = []
        for i in range(10):
            post = Post.objects.create(
                title=f'SEO Test Post {i}',
                content='<p>' + 'Content word ' * 200 + '</p>',
                author=self.user,
                category=self.category,
                status=Post.Status.PUBLISHED
            )
            posts.append(post)
        
        # Test bulk SEO operations
        import time
        start_time = time.time()
        
        for post in posts:
            post.get_keywords()
            post.get_structured_data()
            post.validate_seo()
        
        end_time = time.time()
        
        # Should complete reasonably quickly (less than 1 second for 10 posts)
        self.assertLess(end_time - start_time, 1.0)
        
        # Verify all posts have proper SEO data
        for post in posts:
            self.assertTrue(post.slug)
            self.assertTrue(post.meta_title)
            self.assertTrue(post.meta_description)
            self.assertGreater(post.reading_time, 0)