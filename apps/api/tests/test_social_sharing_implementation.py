"""
Test suite for social sharing and Open Graph implementation.
Tests the enhanced social media features including Open Graph tags, Twitter Cards,
Schema.org markup, and social sharing analytics.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from unittest.mock import patch, MagicMock
from urllib.parse import quote_plus

from apps.blog.models import Post, Category, Tag
from apps.analytics.models import SocialShare
from apps.blog.social_utils import SocialImageGenerator, generate_social_sharing_urls
from apps.blog.templatetags.seo_tags import enhanced_social_meta_tags, enhanced_structured_data

User = get_user_model()


class SocialSharingTestCase(TestCase):
    """Test case for social sharing functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Technology articles'
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Django', slug='django')
        self.tag2 = Tag.objects.create(name='Python', slug='python')
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Blog Post for Social Sharing',
            slug='test-blog-post-social-sharing',
            content='<p>This is a comprehensive test post for social sharing functionality.</p>',
            excerpt='Test post excerpt for social sharing',
            author=self.user,
            category=self.category,
            status='published',
            meta_title='Test Post | Django Blog',
            meta_description='This is a test post for validating social sharing features'
        )
        self.post.tags.add(self.tag1, self.tag2)
    
    def test_enhanced_social_meta_tags_generation(self):
        """Test enhanced social meta tags generation."""
        # Create a mock request
        request = MagicMock()
        request.build_absolute_uri.return_value = 'https://example.com/post/test-blog-post-social-sharing/'
        
        # Generate social meta tags
        meta_tags = enhanced_social_meta_tags(self.post, request)
        
        # Verify Open Graph tags
        self.assertIn('og:title', meta_tags)
        self.assertIn('og:description', meta_tags)
        self.assertIn('og:url', meta_tags)
        self.assertIn('og:type', meta_tags)
        self.assertIn('og:site_name', meta_tags)
        self.assertIn('og:locale', meta_tags)
        
        # Verify Twitter Card tags
        self.assertIn('twitter:card', meta_tags)
        self.assertIn('twitter:title', meta_tags)
        self.assertIn('twitter:description', meta_tags)
        self.assertIn('summary_large_image', meta_tags)
        
        # Verify article-specific tags
        self.assertIn('article:author', meta_tags)
        self.assertIn('article:section', meta_tags)
        self.assertIn('article:tag', meta_tags)
        
        # Verify content includes post data
        self.assertIn(self.post.title, meta_tags)
        self.assertIn(self.post.excerpt, meta_tags)
        self.assertIn(self.category.name, meta_tags)
    
    def test_enhanced_structured_data_generation(self):
        """Test enhanced structured data generation."""
        # Mock the get_structured_data method
        structured_data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": self.post.title,
            "description": self.post.excerpt,
            "author": {
                "@type": "Person",
                "name": self.user.username
            },
            "datePublished": self.post.published_at.isoformat() if self.post.published_at else None,
            "dateModified": self.post.updated_at.isoformat(),
            "url": self.post.get_absolute_url(),
        }
        
        with patch.object(self.post, 'get_structured_data', return_value=structured_data):
            result = enhanced_structured_data(self.post)
            
            # Verify JSON-LD script tag is generated
            self.assertIn('<script type="application/ld+json">', result)
            self.assertIn('"@type": "BlogPosting"', result)
            self.assertIn(self.post.title, result)
    
    def test_social_image_generation(self):
        """Test dynamic social image generation."""
        generator = SocialImageGenerator()
        
        # Test image generation
        image = generator.generate_post_image(
            title=self.post.title,
            subtitle=self.category.name,
            site_name='Test Blog'
        )
        
        # Verify image properties
        self.assertEqual(image.size, (1200, 630))
        self.assertEqual(image.mode, 'RGB')
        
        # Test image saving
        content_file = generator.generate_and_save(
            title=self.post.title,
            subtitle=self.category.name,
            site_name='Test Blog'
        )
        
        self.assertIsNotNone(content_file)
        self.assertTrue(content_file.name.endswith('.png'))
    
    def test_social_sharing_urls_generation(self):
        """Test social sharing URLs generation."""
        # Create a mock request
        request = MagicMock()
        request.build_absolute_uri.return_value = 'https://example.com/post/test-blog-post-social-sharing/'
        
        sharing_urls = generate_social_sharing_urls(self.post, request)
        
        # Verify all expected platforms are included
        expected_platforms = [
            'facebook', 'twitter', 'linkedin', 'reddit', 'pinterest',
            'whatsapp', 'telegram', 'email', 'copy'
        ]
        
        for platform in expected_platforms:
            self.assertIn(platform, sharing_urls)
            self.assertIsInstance(sharing_urls[platform], str)
            self.assertTrue(sharing_urls[platform].startswith('http') or sharing_urls[platform].startswith('mailto:'))
        
        # Verify URL encoding
        encoded_title = quote_plus(self.post.title)
        self.assertIn(encoded_title, sharing_urls['twitter'])
        self.assertIn(encoded_title, sharing_urls['facebook'])
    
    def test_social_image_api_endpoint(self):
        """Test dynamic social image generation API endpoint."""
        url = reverse('blog:generate_social_image')
        
        # Test with valid parameters
        response = self.client.get(url, {
            'title': self.post.title,
            'subtitle': self.category.name,
            'width': 1200,
            'height': 630
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertIn('Cache-Control', response)
        
        # Test with missing title
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
        # Test with invalid dimensions
        response = self.client.get(url, {
            'title': 'Test',
            'width': 5000,  # Too large
            'height': 630
        })
        self.assertEqual(response.status_code, 400)
    
    def test_social_share_tracking(self):
        """Test social share tracking functionality."""
        url = reverse('blog:track_social_share')
        
        # Test valid share tracking
        data = {
            'platform': 'facebook',
            'post_id': self.post.id
        }
        
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify share was recorded
        share = SocialShare.objects.filter(post=self.post, platform='facebook').first()
        self.assertIsNotNone(share)
        self.assertEqual(share.platform, 'facebook')
        
        # Test invalid data
        response = self.client.post(
            url,
            json.dumps({'platform': 'facebook'}),  # Missing post_id
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_share_counts_api(self):
        """Test share counts API endpoint."""
        # Create some test shares
        SocialShare.objects.create(
            post=self.post,
            platform='facebook',
            ip_address='127.0.0.1'
        )
        SocialShare.objects.create(
            post=self.post,
            platform='twitter',
            ip_address='127.0.0.1'
        )
        SocialShare.objects.create(
            post=self.post,
            platform='facebook',
            ip_address='127.0.0.2'
        )
        
        url = reverse('blog:get_share_counts', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['post_id'], self.post.id)
        self.assertEqual(data['total_shares'], 3)
        self.assertIn('share_counts', data)
        self.assertEqual(data['share_counts']['facebook'], 2)
        self.assertEqual(data['share_counts']['twitter'], 1)
    
    def test_social_sharing_debug_endpoint(self):
        """Test social sharing debug endpoint."""
        url = reverse('blog:social_sharing_debug', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify debug data structure
        self.assertIn('post', data)
        self.assertIn('seo', data)
        self.assertIn('open_graph', data)
        self.assertIn('twitter', data)
        self.assertIn('structured_data', data)
        
        # Verify post data
        self.assertEqual(data['post']['title'], self.post.title)
        self.assertEqual(data['post']['slug'], self.post.slug)
        
        # Verify Open Graph data
        self.assertEqual(data['open_graph']['title'], self.post.title)
        self.assertEqual(data['open_graph']['type'], 'article')
    
    def test_post_detail_template_integration(self):
        """Test social sharing integration in post detail template."""
        url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Verify enhanced social meta tags are included
        self.assertIn('og:title', content)
        self.assertIn('og:description', content)
        self.assertIn('twitter:card', content)
        self.assertIn('summary_large_image', content)
        
        # Verify structured data is included
        self.assertIn('application/ld+json', content)
        self.assertIn('"@type": "BlogPosting"', content)
        
        # Verify social sharing buttons are present
        self.assertIn('social-sharing-buttons', content)
        self.assertIn('data-post-id', content)
    
    def test_social_image_preview_endpoint(self):
        """Test social image preview endpoint."""
        url = reverse('blog:social_image_preview', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertIn('no-cache', response['Cache-Control'])
    
    def test_og_image_regeneration(self):
        """Test OG image regeneration endpoint."""
        # Login as the post author
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('blog:regenerate_og_image', kwargs={'post_id': self.post.id})
        
        with patch('apps.core.utils.create_open_graph_image') as mock_create_image:
            mock_content = MagicMock()
            mock_create_image.return_value = mock_content
            
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            
            # Verify the function was called
            mock_create_image.assert_called_once()
    
    def test_social_image_validation(self):
        """Test social image validation endpoint."""
        url = reverse('blog:validate_social_image')
        
        response = self.client.get(url, {'url': 'https://example.com/image.png'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify validation structure
        self.assertIn('width', data)
        self.assertIn('height', data)
        self.assertIn('recommendations', data)
        self.assertIn('facebook', data['recommendations'])
        self.assertIn('twitter', data['recommendations'])
    
    def test_social_sharing_analytics_tracking(self):
        """Test comprehensive social sharing analytics."""
        from apps.blog.social_utils import SocialSharingAnalytics
        
        # Track a share
        request = MagicMock()
        request.user.is_authenticated = True
        request.user = self.user
        request.META = {'HTTP_USER_AGENT': 'Test Browser'}
        
        with patch('apps.core.utils.get_client_ip', return_value='127.0.0.1'):
            SocialSharingAnalytics.track_share(self.post, 'facebook', request)
        
        # Verify share was tracked
        share = SocialShare.objects.filter(post=self.post, platform='facebook').first()
        self.assertIsNotNone(share)
        self.assertEqual(share.user, self.user)
        self.assertEqual(share.ip_address, '127.0.0.1')
        
        # Test share counts retrieval
        share_counts = SocialSharingAnalytics.get_share_counts(self.post)
        self.assertEqual(share_counts['facebook'], 1)
    
    def test_template_tag_error_handling(self):
        """Test template tag error handling."""
        # Test with None object
        result = enhanced_social_meta_tags(None, None)
        self.assertEqual(result, '')
        
        # Test with object without required methods
        mock_obj = MagicMock()
        del mock_obj.get_seo_title
        del mock_obj.title
        
        result = enhanced_social_meta_tags(mock_obj, None)
        self.assertIsInstance(result, str)
    
    def test_social_sharing_buttons_template(self):
        """Test social sharing buttons template rendering."""
        from django.template import Template, Context
        
        template = Template("""
            {% load seo_tags %}
            {% enhanced_social_sharing_buttons post %}
        """)
        
        context = Context({
            'post': self.post,
            'request': MagicMock()
        })
        
        rendered = template.render(context)
        
        # Verify social buttons are rendered
        self.assertIn('social-sharing-buttons', rendered)
        self.assertIn('data-post-id', rendered)
        self.assertIn('facebook', rendered)
        self.assertIn('twitter', rendered)
    
    def test_breadcrumb_structured_data(self):
        """Test breadcrumb structured data generation."""
        from apps.blog.templatetags.seo_tags import breadcrumb_structured_data
        
        breadcrumbs = [
            {'name': 'Home', 'url': '/'},
            {'name': 'Blog', 'url': '/blog/'},
            {'name': 'Technology', 'url': '/category/technology/'},
            {'name': self.post.title, 'url': self.post.get_absolute_url()}
        ]
        
        result = breadcrumb_structured_data(breadcrumbs)
        
        self.assertIn('application/ld+json', result)
        self.assertIn('"@type": "BreadcrumbList"', result)
        self.assertIn('"position": 1', result)
        self.assertIn(self.post.title, result)


class SocialImageGeneratorTestCase(TestCase):
    """Test case for social image generation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.generator = SocialImageGenerator()
    
    def test_image_generation_with_different_parameters(self):
        """Test image generation with various parameters."""
        # Test basic generation
        image = self.generator.generate_post_image("Test Title")
        self.assertEqual(image.size, (1200, 630))
        
        # Test with subtitle
        image = self.generator.generate_post_image("Test Title", "Test Subtitle")
        self.assertEqual(image.size, (1200, 630))
        
        # Test with site name
        image = self.generator.generate_post_image("Test Title", site_name="Test Site")
        self.assertEqual(image.size, (1200, 630))
    
    def test_text_wrapping(self):
        """Test text wrapping functionality."""
        long_title = "This is a very long title that should be wrapped across multiple lines to fit within the image boundaries"
        
        # Mock font for testing
        mock_font = MagicMock()
        mock_font.getbbox.return_value = (0, 0, 800, 50)  # width, height
        
        wrapped_lines = self.generator.wrap_text(long_title, mock_font, 600)
        
        self.assertIsInstance(wrapped_lines, list)
        self.assertGreater(len(wrapped_lines), 1)
    
    def test_fallback_image_generation(self):
        """Test fallback image generation."""
        fallback_image = self.generator._generate_fallback_image("Test Title")
        
        self.assertEqual(fallback_image.size, (1200, 630))
        self.assertEqual(fallback_image.mode, 'RGB')
    
    def test_image_saving(self):
        """Test image saving functionality."""
        image = self.generator.generate_post_image("Test Title")
        img_io = self.generator.save_image(image)
        
        self.assertIsNotNone(img_io)
        self.assertGreater(img_io.tell(), 0)  # Verify content was written


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'apps.core',
                'apps.blog',
                'apps.analytics',
            ],
            SECRET_KEY='test-secret-key',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])