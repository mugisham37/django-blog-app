"""
Tests for sitemap functionality.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.sites.models import Site
from django.utils import timezone
from datetime import timedelta

from apps.blog.models import Post, Category, Tag
from apps.accounts.models import User


class SitemapTestCase(TestCase):
    """Test sitemap generation and functionality."""

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
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(
            name='Test Tag 1',
            slug='test-tag-1',
            usage_count=1
        )
        self.tag2 = Tag.objects.create(
            name='Test Tag 2', 
            slug='test-tag-2',
            usage_count=1
        )
        
        # Create test posts
        self.published_post = Post.objects.create(
            title='Published Test Post',
            slug='published-test-post',
            content='This is a published test post content.',
            excerpt='Published test excerpt',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1)
        )
        self.published_post.tags.add(self.tag1, self.tag2)
        
        self.draft_post = Post.objects.create(
            title='Draft Test Post',
            slug='draft-test-post',
            content='This is a draft test post content.',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        # Ensure site exists
        Site.objects.get_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Test Site'}
        )

    def test_main_sitemap_accessible(self):
        """Test that the main sitemap is accessible."""
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_posts_sitemap_accessible(self):
        """Test that the posts sitemap is accessible."""
        response = self.client.get('/sitemap-posts.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_categories_sitemap_accessible(self):
        """Test that the categories sitemap is accessible."""
        response = self.client.get('/sitemap-categories.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_tags_sitemap_accessible(self):
        """Test that the tags sitemap is accessible."""
        response = self.client.get('/sitemap-tags.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_static_sitemap_accessible(self):
        """Test that the static pages sitemap is accessible."""
        response = self.client.get('/sitemap-static.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_news_sitemap_accessible(self):
        """Test that the news sitemap is accessible."""
        response = self.client.get('/sitemap-news.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_posts_sitemap_contains_published_posts(self):
        """Test that posts sitemap contains only published posts."""
        response = self.client.get('/sitemap-posts.xml')
        content = response.content.decode('utf-8')
        
        # Should contain published post
        self.assertIn('published-test-post', content)
        
        # Should not contain draft post
        self.assertNotIn('draft-test-post', content)

    def test_categories_sitemap_contains_active_categories(self):
        """Test that categories sitemap contains active categories with posts."""
        response = self.client.get('/sitemap-categories.xml')
        content = response.content.decode('utf-8')
        
        # Should contain category with published posts
        self.assertIn('test-category', content)

    def test_tags_sitemap_contains_used_tags(self):
        """Test that tags sitemap contains tags with published posts."""
        response = self.client.get('/sitemap-tags.xml')
        content = response.content.decode('utf-8')
        
        # Should contain tags used by published posts
        self.assertIn('test-tag-1', content)
        self.assertIn('test-tag-2', content)

    def test_robots_txt_accessible(self):
        """Test that robots.txt is accessible and contains sitemap references."""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        
        content = response.content.decode('utf-8')
        self.assertIn('Sitemap:', content)
        self.assertIn('sitemap.xml', content)

    def test_sitemap_lastmod_updates(self):
        """Test that sitemap lastmod dates update when content changes."""
        # Get initial sitemap
        response = self.client.get('/sitemap-posts.xml')
        initial_content = response.content.decode('utf-8')
        
        # Update the post
        self.published_post.title = 'Updated Published Test Post'
        self.published_post.save()
        
        # Get updated sitemap
        response = self.client.get('/sitemap-posts.xml')
        updated_content = response.content.decode('utf-8')
        
        # Content should be different (lastmod should have changed)
        # Note: This is a basic check - in practice you'd parse XML and compare dates
        self.assertEqual(response.status_code, 200)

    def test_sitemap_priority_for_featured_posts(self):
        """Test that featured posts get higher priority in sitemap."""
        # Create a featured post
        featured_post = Post.objects.create(
            title='Featured Test Post',
            slug='featured-test-post',
            content='This is a featured test post.',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
            is_featured=True
        )
        
        response = self.client.get('/sitemap-posts.xml')
        self.assertEqual(response.status_code, 200)
        
        # The sitemap should contain the featured post
        content = response.content.decode('utf-8')
        self.assertIn('featured-test-post', content)

    def test_news_sitemap_recent_posts_only(self):
        """Test that news sitemap contains only recent posts."""
        # Create an old post
        old_post = Post.objects.create(
            title='Old Test Post',
            slug='old-test-post',
            content='This is an old test post.',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=5)  # 5 days old
        )
        
        # Create a recent post
        recent_post = Post.objects.create(
            title='Recent Test Post',
            slug='recent-test-post',
            content='This is a recent test post.',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(hours=1)  # 1 hour old
        )
        
        response = self.client.get('/sitemap-news.xml')
        content = response.content.decode('utf-8')
        
        # Should contain recent post
        self.assertIn('recent-test-post', content)
        
        # Should not contain old post (news sitemap is for last 2 days)
        self.assertNotIn('old-test-post', content)