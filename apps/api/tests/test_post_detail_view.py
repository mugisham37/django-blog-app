"""
Tests for PostDetailView functionality and related content algorithms.
"""

import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from apps.blog.models import Post, Category, Tag
from apps.comments.models import Comment
from apps.core.utils import generate_slug_with_validation

User = get_user_model()


class PostDetailViewTestCase(TestCase):
    """
    Test cases for PostDetailView functionality.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = Client()
        
        # Create test users
        self.author = User.objects.create_user(
            username='testauthor',
            email='author@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Author'
        )
        
        self.commenter = User.objects.create_user(
            username='commenter',
            email='commenter@test.com',
            password='testpass123'
        )
        
        # Create test categories
        self.parent_category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Technology articles'
        )
        
        self.child_category = Category.objects.create(
            name='Python',
            slug='python',
            description='Python programming',
            parent=self.parent_category
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Django', slug='django', color='#007bff')
        self.tag2 = Tag.objects.create(name='Web Development', slug='web-development', color='#28a745')
        self.tag3 = Tag.objects.create(name='Python', slug='python-tag', color='#ffc107')
        
        # Create test posts
        self.main_post = Post.objects.create(
            title='Django Best Practices',
            slug='django-best-practices',
            content='<p>This is a comprehensive guide to Django best practices.</p>' * 10,
            excerpt='Learn Django best practices in this comprehensive guide.',
            author=self.author,
            category=self.child_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
            featured_image=None,
            allow_comments=True
        )
        self.main_post.tags.set([self.tag1, self.tag2])
        
        # Create related posts for testing algorithm
        self.related_post1 = Post.objects.create(
            title='Advanced Django Techniques',
            slug='advanced-django-techniques',
            content='<p>Advanced Django development techniques.</p>' * 5,
            author=self.author,
            category=self.child_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1)
        )
        self.related_post1.tags.set([self.tag1, self.tag3])  # Shares Django tag
        
        self.related_post2 = Post.objects.create(
            title='Web Development Fundamentals',
            slug='web-development-fundamentals',
            content='<p>Web development fundamentals.</p>' * 5,
            author=self.author,
            category=self.parent_category,  # Same parent category
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=2)
        )
        self.related_post2.tags.set([self.tag2])  # Shares Web Development tag
        
        self.unrelated_post = Post.objects.create(
            title='Cooking Tips',
            slug='cooking-tips',
            content='<p>Great cooking tips.</p>' * 5,
            author=self.author,
            category=None,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=3)
        )
        # No shared tags or category
        
        # Create draft post (should not appear in related)
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            content='<p>This is a draft.</p>',
            author=self.author,
            status=Post.Status.DRAFT
        )
        
        # Create comments
        self.comment1 = Comment.objects.create(
            content='Great article! Very helpful.',
            author=self.commenter,
            post=self.main_post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.comment2 = Comment.objects.create(
            content='I agree with the previous comment.',
            author=self.author,
            post=self.main_post,
            parent=self.comment1,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.unapproved_comment = Comment.objects.create(
            content='This should not appear.',
            author=self.commenter,
            post=self.main_post,
            ip_address='127.0.0.1',
            is_approved=False
        )
    
    def test_post_detail_view_basic_functionality(self):
        """
        Test basic PostDetailView functionality.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.main_post.title)
        self.assertContains(response, self.main_post.content)
        self.assertContains(response, self.main_post.excerpt)
        self.assertContains(response, self.author.get_full_name())
    
    def test_view_count_increment(self):
        """
        Test that view count is incremented when post is viewed.
        """
        initial_view_count = self.main_post.view_count
        
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        self.client.get(url)
        
        # Refresh from database
        self.main_post.refresh_from_db()
        self.assertEqual(self.main_post.view_count, initial_view_count + 1)
    
    def test_related_posts_algorithm(self):
        """
        Test the related posts suggestion algorithm.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        related_posts = response.context['related_posts']
        
        # Should include posts with shared tags/category
        self.assertIn(self.related_post1, related_posts)  # Shares Django tag
        self.assertIn(self.related_post2, related_posts)  # Shares Web Development tag
        
        # Should not include unrelated posts
        self.assertNotIn(self.unrelated_post, related_posts)
        
        # Should not include draft posts
        self.assertNotIn(self.draft_post, related_posts)
        
        # Should not include the current post
        self.assertNotIn(self.main_post, related_posts)
    
    def test_related_posts_ordering(self):
        """
        Test that related posts are ordered by relevance.
        """
        # Create a post with more shared tags (higher relevance)
        high_relevance_post = Post.objects.create(
            title='Django and Web Development Guide',
            slug='django-web-dev-guide',
            content='<p>Django and web development guide.</p>' * 5,
            author=self.author,
            category=self.child_category,  # Same category
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(hours=1)
        )
        high_relevance_post.tags.set([self.tag1, self.tag2])  # Shares both tags
        
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        related_posts = response.context['related_posts']
        
        # High relevance post should be first
        self.assertEqual(related_posts[0], high_relevance_post)
    
    def test_breadcrumb_navigation(self):
        """
        Test breadcrumb navigation generation.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        breadcrumbs = response.context['breadcrumbs']
        
        # Should include Home, Blog, category hierarchy, and current post
        self.assertEqual(breadcrumbs[0]['title'], 'Home')
        self.assertEqual(breadcrumbs[1]['title'], 'Blog')
        self.assertEqual(breadcrumbs[2]['title'], 'Technology')  # Parent category
        self.assertEqual(breadcrumbs[3]['title'], 'Python')     # Child category
        self.assertEqual(breadcrumbs[4]['title'], self.main_post.title)
        self.assertTrue(breadcrumbs[4].get('current', False))
    
    def test_breadcrumb_without_category(self):
        """
        Test breadcrumb navigation for post without category.
        """
        post_without_category = Post.objects.create(
            title='Post Without Category',
            slug='post-without-category',
            content='<p>Content here.</p>',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        url = reverse('blog:post_detail', kwargs={'slug': post_without_category.slug})
        response = self.client.get(url)
        
        breadcrumbs = response.context['breadcrumbs']
        
        # Should only include Home, Blog, and current post
        self.assertEqual(len(breadcrumbs), 3)
        self.assertEqual(breadcrumbs[0]['title'], 'Home')
        self.assertEqual(breadcrumbs[1]['title'], 'Blog')
        self.assertEqual(breadcrumbs[2]['title'], post_without_category.title)
    
    def test_social_sharing_data(self):
        """
        Test social sharing data generation.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        social_sharing = response.context['social_sharing']
        
        # Check required fields
        self.assertIn('url', social_sharing)
        self.assertIn('title', social_sharing)
        self.assertIn('description', social_sharing)
        self.assertIn('twitter', social_sharing)
        self.assertIn('facebook', social_sharing)
        self.assertIn('linkedin', social_sharing)
        
        # Check Twitter URL format
        self.assertIn('twitter.com/intent/tweet', social_sharing['twitter']['url'])
        self.assertIn('facebook.com/sharer', social_sharing['facebook']['url'])
    
    def test_comment_display(self):
        """
        Test comment display functionality.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        # Check approved comments are displayed
        self.assertContains(response, self.comment1.content)
        self.assertContains(response, self.comment2.content)
        
        # Check unapproved comments are not displayed
        self.assertNotContains(response, self.unapproved_comment.content)
        
        # Check comment count
        self.assertEqual(response.context['comment_count'], 2)  # Only approved comments
    
    def test_comment_form_for_authenticated_user(self):
        """
        Test comment form display for authenticated users.
        """
        self.client.login(username='commenter', password='testpass123')
        
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        self.assertTrue(response.context['user_can_comment'])
        self.assertIsNotNone(response.context['comment_form'])
        self.assertContains(response, 'Leave a Comment')
    
    def test_comment_form_for_anonymous_user(self):
        """
        Test comment form behavior for anonymous users.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        # Assuming COMMENTS_REQUIRE_LOGIN is True (default behavior)
        self.assertFalse(response.context['user_can_comment'])
        self.assertContains(response, 'Login')
    
    def test_post_navigation(self):
        """
        Test previous/next post navigation.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        # Check navigation context
        self.assertIn('previous_post', response.context)
        self.assertIn('next_post', response.context)
        
        # The main post is the newest, so it should have previous posts but no next post
        self.assertIsNotNone(response.context['previous_post'])
        self.assertIsNone(response.context['next_post'])
    
    def test_seo_metadata(self):
        """
        Test SEO metadata in response.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        # Check structured data
        self.assertIn('structured_data', response.context)
        structured_data = response.context['structured_data']
        self.assertEqual(structured_data['@type'], 'BlogPosting')
        self.assertEqual(structured_data['headline'], self.main_post.title)
        
        # Check SEO keywords
        self.assertIn('seo_keywords', response.context)
        keywords = response.context['seo_keywords']
        self.assertIn('Django', keywords)
        self.assertIn('Web Development', keywords)
    
    def test_reading_progress_data(self):
        """
        Test reading progress data.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        reading_progress = response.context['reading_progress']
        
        self.assertIn('reading_time', reading_progress)
        self.assertIn('word_count', reading_progress)
        self.assertIn('estimated_words_per_minute', reading_progress)
        self.assertEqual(reading_progress['estimated_words_per_minute'], 200)
    
    def test_post_metadata(self):
        """
        Test post metadata context.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        post_metadata = response.context['post_metadata']
        
        self.assertEqual(post_metadata['published_date'], self.main_post.published_at)
        self.assertEqual(post_metadata['last_modified'], self.main_post.updated_at)
        self.assertGreaterEqual(post_metadata['view_count'], 1)  # Should be incremented
    
    def test_draft_post_not_accessible(self):
        """
        Test that draft posts are not accessible via detail view.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.draft_post.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_nonexistent_post_404(self):
        """
        Test 404 response for nonexistent posts.
        """
        url = reverse('blog:post_detail', kwargs={'slug': 'nonexistent-post'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_comments_disabled_post(self):
        """
        Test behavior when comments are disabled for a post.
        """
        self.main_post.allow_comments = False
        self.main_post.save()
        
        url = reverse('blog:post_detail', kwargs={'slug': self.main_post.slug})
        response = self.client.get(url)
        
        self.assertFalse(response.context['comments_enabled'])
        self.assertNotContains(response, 'Leave a Comment')


class RelatedPostsAlgorithmTestCase(TestCase):
    """
    Specific tests for the related posts algorithm.
    """
    
    def setUp(self):
        """
        Set up test data for algorithm testing.
        """
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        # Create categories
        self.tech_category = Category.objects.create(name='Technology', slug='tech')
        self.python_category = Category.objects.create(
            name='Python',
            slug='python',
            parent=self.tech_category
        )
        
        # Create tags
        self.django_tag = Tag.objects.create(name='Django', slug='django')
        self.python_tag = Tag.objects.create(name='Python', slug='python-tag')
        self.web_tag = Tag.objects.create(name='Web', slug='web')
        self.api_tag = Tag.objects.create(name='API', slug='api')
        
        # Main post
        self.main_post = Post.objects.create(
            title='Django REST API Guide',
            slug='django-rest-api-guide',
            content='<p>Django REST API development guide.</p>',
            author=self.author,
            category=self.python_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        self.main_post.tags.set([self.django_tag, self.python_tag, self.api_tag])
    
    def test_algorithm_with_multiple_shared_tags(self):
        """
        Test algorithm prioritizes posts with more shared tags.
        """
        # Post with 2 shared tags (higher relevance)
        high_relevance = Post.objects.create(
            title='Django Python Best Practices',
            slug='django-python-best-practices',
            content='<p>Best practices.</p>',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1)
        )
        high_relevance.tags.set([self.django_tag, self.python_tag])
        
        # Post with 1 shared tag (lower relevance)
        low_relevance = Post.objects.create(
            title='Web Development Basics',
            slug='web-development-basics',
            content='<p>Web basics.</p>',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=2)
        )
        low_relevance.tags.set([self.django_tag])
        
        from apps.blog.views import PostDetailView
        view = PostDetailView()
        related_posts = view.get_related_posts(self.main_post, limit=4)
        
        # High relevance should come first
        self.assertEqual(related_posts[0], high_relevance)
        self.assertEqual(related_posts[1], low_relevance)
    
    def test_algorithm_with_same_category(self):
        """
        Test algorithm considers same category.
        """
        # Post in same category but no shared tags
        same_category_post = Post.objects.create(
            title='Python Fundamentals',
            slug='python-fundamentals',
            content='<p>Python basics.</p>',
            author=self.author,
            category=self.python_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1)
        )
        # No shared tags
        
        # Post with no category but shared tag
        shared_tag_post = Post.objects.create(
            title='Django Tutorial',
            slug='django-tutorial',
            content='<p>Django tutorial.</p>',
            author=self.author,
            category=None,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=2)
        )
        shared_tag_post.tags.set([self.django_tag])
        
        from apps.blog.views import PostDetailView
        view = PostDetailView()
        related_posts = view.get_related_posts(self.main_post, limit=4)
        
        # Shared tag should have higher relevance than same category alone
        self.assertEqual(related_posts[0], shared_tag_post)
        self.assertEqual(related_posts[1], same_category_post)
    
    def test_algorithm_fallback_to_recent_posts(self):
        """
        Test algorithm falls back to recent posts when no related content.
        """
        # Create posts with no shared tags or categories
        recent_post1 = Post.objects.create(
            title='Cooking Tips',
            slug='cooking-tips',
            content='<p>Cooking tips.</p>',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1)
        )
        
        recent_post2 = Post.objects.create(
            title='Travel Guide',
            slug='travel-guide',
            content='<p>Travel guide.</p>',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=2)
        )
        
        from apps.blog.views import PostDetailView
        view = PostDetailView()
        related_posts = view.get_related_posts(self.main_post, limit=4)
        
        # Should include recent posts as fallback
        self.assertIn(recent_post1, related_posts)
        self.assertIn(recent_post2, related_posts)
        
        # More recent should come first
        self.assertEqual(related_posts[0], recent_post1)
    
    def test_algorithm_respects_limit(self):
        """
        Test algorithm respects the limit parameter.
        """
        # Create more posts than the limit
        for i in range(10):
            Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content=f'<p>Test content {i}.</p>',
                author=self.author,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now() - timedelta(days=i+1)
            )
        
        from apps.blog.views import PostDetailView
        view = PostDetailView()
        related_posts = view.get_related_posts(self.main_post, limit=3)
        
        # Should return exactly 3 posts
        self.assertEqual(len(related_posts), 3)
    
    def test_algorithm_excludes_current_post(self):
        """
        Test algorithm never includes the current post.
        """
        from apps.blog.views import PostDetailView
        view = PostDetailView()
        related_posts = view.get_related_posts(self.main_post, limit=10)
        
        # Should never include the main post itself
        self.assertNotIn(self.main_post, related_posts)


class PostDetailViewIntegrationTestCase(TestCase):
    """
    Integration tests for PostDetailView with all components.
    """
    
    def setUp(self):
        """
        Set up comprehensive test data.
        """
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Technology articles'
        )
        
        self.tag = Tag.objects.create(
            name='Django',
            slug='django',
            color='#007bff'
        )
        
        self.post = Post.objects.create(
            title='Complete Django Guide',
            slug='complete-django-guide',
            content='<p>This is a comprehensive Django guide with lots of useful information.</p>' * 20,
            excerpt='Learn Django from scratch with this comprehensive guide.',
            author=self.author,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
            meta_title='Complete Django Guide - Learn Django',
            meta_description='Comprehensive Django tutorial covering all aspects of Django development.',
            allow_comments=True
        )
        self.post.tags.set([self.tag])
    
    def test_complete_post_detail_response(self):
        """
        Test complete post detail response with all features.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check all context variables are present
        expected_context_keys = [
            'post', 'related_posts', 'previous_post', 'next_post',
            'breadcrumbs', 'social_sharing', 'comments', 'comment_count',
            'comment_form', 'comments_enabled', 'user_can_comment',
            'structured_data', 'seo_keywords', 'reading_progress',
            'post_metadata'
        ]
        
        for key in expected_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
        
        # Check HTML content includes key elements
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content)
        self.assertContains(response, 'breadcrumb')
        self.assertContains(response, 'social-sharing')
        self.assertContains(response, 'reading-progress')
        self.assertContains(response, 'application/ld+json')  # Structured data
    
    def test_seo_meta_tags_in_html(self):
        """
        Test SEO meta tags are properly rendered in HTML.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        
        # Check meta tags
        self.assertContains(response, f'<title>{self.post.meta_title}</title>')
        self.assertContains(response, f'<meta name="description" content="{self.post.meta_description}">')
        self.assertContains(response, 'property="og:title"')
        self.assertContains(response, 'property="og:description"')
        self.assertContains(response, 'property="og:type" content="article"')
    
    def test_javascript_functionality_included(self):
        """
        Test JavaScript functionality is included in response.
        """
        url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        
        # Check JavaScript code is present
        self.assertContains(response, 'reading-progress')
        self.assertContains(response, 'social-btn')
        self.assertContains(response, 'updateProgress')
        self.assertContains(response, 'copyToClipboard')