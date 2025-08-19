"""
Tests for blog post scheduling and publishing workflow.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore

from apps.blog.models import Post, Category, Tag, PostPreviewToken
from apps.blog.admin import PostAdmin
from apps.blog.tasks import (
    publish_scheduled_posts, 
    bulk_update_post_status, 
    schedule_post_publication,
    cleanup_expired_preview_tokens,
    notify_author_post_published
)

User = get_user_model()


class PostSchedulingModelTests(TestCase):
    """
    Test post scheduling functionality at the model level.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
    def test_post_can_be_scheduled(self):
        """Test that a post can be scheduled for future publication."""
        future_time = timezone.now() + timedelta(hours=1)
        
        post = Post.objects.create(
            title='Scheduled Post',
            content='This is a scheduled post.',
            author=self.user,
            status=Post.Status.SCHEDULED,
            published_at=future_time
        )
        
        self.assertEqual(post.status, Post.Status.SCHEDULED)
        self.assertEqual(post.published_at, future_time)
        self.assertFalse(post.is_published())
    
    def test_scheduled_post_validation(self):
        """Test validation for scheduled posts."""
        # Test that scheduled posts require a future publish date
        with self.assertRaises(Exception):
            post = Post(
                title='Invalid Scheduled Post',
                content='Content',
                author=self.user,
                status=Post.Status.SCHEDULED,
                published_at=timezone.now() - timedelta(hours=1)  # Past date
            )
            post.full_clean()
    
    def test_post_status_display_with_schedule(self):
        """Test status display includes scheduling information."""
        future_time = timezone.now() + timedelta(hours=2)
        
        post = Post.objects.create(
            title='Scheduled Post',
            content='Content',
            author=self.user,
            status=Post.Status.SCHEDULED,
            published_at=future_time
        )
        
        status_display = post.get_status_display_with_date()
        self.assertIn('Scheduled', status_display)
        self.assertIn(future_time.strftime('%B %d, %Y'), status_display)
    
    def test_post_can_be_published_validation(self):
        """Test validation for posts that can be published."""
        # Valid post
        post = Post.objects.create(
            title='Valid Post',
            content='This post has all required fields.',
            author=self.user
        )
        self.assertTrue(post.can_be_published())
        
        # Invalid post - no title
        post_no_title = Post.objects.create(
            title='',
            content='Content without title',
            author=self.user
        )
        self.assertFalse(post_no_title.can_be_published())
        
        # Invalid post - no content
        post_no_content = Post.objects.create(
            title='Title without content',
            content='',
            author=self.user
        )
        self.assertFalse(post_no_content.can_be_published())


class PostPreviewTokenTests(TestCase):
    """
    Test preview token functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            status=Post.Status.DRAFT
        )
    
    def test_create_preview_token(self):
        """Test creating a preview token."""
        token = PostPreviewToken.create_token(
            post=self.post,
            created_by=self.user,
            expires_in_hours=24,
            max_access_count=10
        )
        
        self.assertEqual(token.post, self.post)
        self.assertEqual(token.created_by, self.user)
        self.assertEqual(token.max_access_count, 10)
        self.assertTrue(token.is_active)
        self.assertTrue(token.is_valid())
    
    def test_preview_token_expiration(self):
        """Test that preview tokens expire correctly."""
        # Create expired token
        token = PostPreviewToken.objects.create(
            post=self.post,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
            max_access_count=10
        )
        
        self.assertFalse(token.is_valid())
    
    def test_preview_token_access_limit(self):
        """Test that preview tokens respect access limits."""
        token = PostPreviewToken.create_token(
            post=self.post,
            created_by=self.user,
            expires_in_hours=24,
            max_access_count=2
        )
        
        # First access
        token.increment_access_count()
        self.assertTrue(token.is_valid())
        
        # Second access
        token.increment_access_count()
        self.assertFalse(token.is_valid())  # Should be invalid after max uses
    
    def test_preview_token_deactivation(self):
        """Test deactivating preview tokens."""
        token = PostPreviewToken.create_token(
            post=self.post,
            created_by=self.user
        )
        
        self.assertTrue(token.is_valid())
        
        token.deactivate()
        self.assertFalse(token.is_valid())
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Create expired token
        expired_token = PostPreviewToken.objects.create(
            post=self.post,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
            max_access_count=10
        )
        
        # Create valid token
        valid_token = PostPreviewToken.create_token(
            post=self.post,
            created_by=self.user
        )
        
        # Cleanup expired tokens
        deleted_count = PostPreviewToken.cleanup_expired_tokens()
        
        self.assertEqual(deleted_count, 1)
        self.assertFalse(PostPreviewToken.objects.filter(id=expired_token.id).exists())
        self.assertTrue(PostPreviewToken.objects.filter(id=valid_token.id).exists())


class CeleryTaskTests(TransactionTestCase):
    """
    Test Celery tasks for post scheduling and publishing.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
    
    def test_publish_scheduled_posts_task(self):
        """Test the publish_scheduled_posts Celery task."""
        # Create scheduled post that should be published
        past_time = timezone.now() - timedelta(minutes=5)
        scheduled_post = Post.objects.create(
            title='Scheduled Post',
            content='This should be published.',
            author=self.user,
            status=Post.Status.SCHEDULED,
            published_at=past_time
        )
        
        # Create scheduled post that should NOT be published (future)
        future_time = timezone.now() + timedelta(hours=1)
        future_post = Post.objects.create(
            title='Future Post',
            content='This should remain scheduled.',
            author=self.user,
            status=Post.Status.SCHEDULED,
            published_at=future_time
        )
        
        # Run the task
        with patch('apps.blog.tasks.notify_author_post_published.delay') as mock_notify:
            result = publish_scheduled_posts()
        
        # Check results
        scheduled_post.refresh_from_db()
        future_post.refresh_from_db()
        
        self.assertEqual(scheduled_post.status, Post.Status.PUBLISHED)
        self.assertEqual(future_post.status, Post.Status.SCHEDULED)
        self.assertEqual(result['published_count'], 1)
        mock_notify.assert_called_once_with(scheduled_post.id)
    
    def test_bulk_update_post_status_task(self):
        """Test the bulk_update_post_status Celery task."""
        # Create draft posts
        post1 = Post.objects.create(
            title='Draft Post 1',
            content='Content 1',
            author=self.user,
            status=Post.Status.DRAFT
        )
        post2 = Post.objects.create(
            title='Draft Post 2',
            content='Content 2',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        # Run bulk update task
        result = bulk_update_post_status(
            [post1.id, post2.id],
            Post.Status.PUBLISHED,
            self.user.id
        )
        
        # Check results
        post1.refresh_from_db()
        post2.refresh_from_db()
        
        self.assertEqual(post1.status, Post.Status.PUBLISHED)
        self.assertEqual(post2.status, Post.Status.PUBLISHED)
        self.assertEqual(result['updated_count'], 2)
        self.assertEqual(len(result['failed_posts']), 0)
    
    def test_schedule_post_publication_task(self):
        """Test the schedule_post_publication Celery task."""
        post = Post.objects.create(
            title='Draft Post',
            content='Content to be scheduled',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        future_time = timezone.now() + timedelta(hours=2)
        
        # Run scheduling task
        result = schedule_post_publication(post.id, future_time.isoformat())
        
        # Check results
        post.refresh_from_db()
        
        self.assertEqual(post.status, Post.Status.SCHEDULED)
        self.assertEqual(post.published_at.replace(microsecond=0), 
                        future_time.replace(microsecond=0))
        self.assertEqual(result['post_id'], post.id)
    
    def test_cleanup_expired_preview_tokens_task(self):
        """Test the cleanup_expired_preview_tokens Celery task."""
        post = Post.objects.create(
            title='Test Post',
            content='Content',
            author=self.user
        )
        
        # Create expired token
        expired_token = PostPreviewToken.objects.create(
            post=post,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=25),  # Older than 24 hours
            max_access_count=10
        )
        
        # Create recent token
        recent_token = PostPreviewToken.create_token(
            post=post,
            created_by=self.user
        )
        
        # Run cleanup task
        result = cleanup_expired_preview_tokens()
        
        # Check results
        self.assertEqual(result['deleted_count'], 1)
        self.assertFalse(PostPreviewToken.objects.filter(id=expired_token.id).exists())
        self.assertTrue(PostPreviewToken.objects.filter(id=recent_token.id).exists())
    
    @patch('apps.blog.tasks.send_mail')
    def test_notify_author_post_published_task(self, mock_send_mail):
        """Test the notify_author_post_published Celery task."""
        post = Post.objects.create(
            title='Published Post',
            content='Content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        # Run notification task
        notify_author_post_published(post.id)
        
        # Check that email was sent
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        
        self.assertIn('Published Post', kwargs['subject'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])


class AdminSchedulingTests(TestCase):
    """
    Test admin interface scheduling functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.author,
            status=Post.Status.DRAFT
        )
        
        self.site = AdminSite()
        self.admin = PostAdmin(Post, self.site)
    
    def test_status_with_schedule_display(self):
        """Test the status_with_schedule admin display method."""
        # Test scheduled post
        future_time = timezone.now() + timedelta(hours=2)
        scheduled_post = Post.objects.create(
            title='Scheduled Post',
            content='Content',
            author=self.author,
            status=Post.Status.SCHEDULED,
            published_at=future_time
        )
        
        status_display = self.admin.status_with_schedule(scheduled_post)
        self.assertIn('Scheduled', status_display)
        self.assertIn('color: #ffc107', status_display)  # Warning color
        
        # Test published post
        published_post = Post.objects.create(
            title='Published Post',
            content='Content',
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        status_display = self.admin.status_with_schedule(published_post)
        self.assertIn('Published', status_display)
        self.assertIn('color: #28a745', status_display)  # Success color
    
    def test_preview_actions_display(self):
        """Test the preview_actions admin display method."""
        actions_html = self.admin.preview_actions(self.post)
        
        self.assertIn('Preview', actions_html)
        self.assertIn('Schedule', actions_html)  # Should show for draft posts
        self.assertIn('Share Preview', actions_html)
    
    def test_bulk_schedule_posts_action(self):
        """Test the bulk_schedule_posts admin action."""
        # Create mock request
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        
        # Add session and messages
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        
        # Create queryset with draft posts
        draft_posts = Post.objects.filter(status=Post.Status.DRAFT)
        
        # Run the action
        response = self.admin.bulk_schedule_posts(request, draft_posts)
        
        # Should redirect to bulk schedule view
        self.assertEqual(response.status_code, 302)
        self.assertIn('bulk-schedule', response.url)


class SchedulingViewTests(TestCase):
    """
    Test views related to post scheduling and preview.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            status=Post.Status.DRAFT
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_post_preview_view(self):
        """Test the post preview view."""
        url = reverse('blog:post_preview', kwargs={'pk': self.post.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertContains(response, 'Preview Mode')
    
    def test_post_preview_token_view_valid_token(self):
        """Test accessing post via valid preview token."""
        # Create preview token
        token = PostPreviewToken.create_token(
            post=self.post,
            created_by=self.user,
            expires_in_hours=24,
            max_access_count=10
        )
        
        url = reverse('blog:post_preview_token', kwargs={'token': token.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertContains(response, 'Preview Mode')
        
        # Check that access count was incremented
        token.refresh_from_db()
        self.assertEqual(token.access_count, 1)
    
    def test_post_preview_token_view_invalid_token(self):
        """Test accessing post via invalid preview token."""
        invalid_token = uuid.uuid4()
        url = reverse('blog:post_preview_token', kwargs={'token': invalid_token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preview Not Available')
        self.assertContains(response, 'Invalid or expired preview link')
    
    def test_post_preview_token_view_expired_token(self):
        """Test accessing post via expired preview token."""
        # Create expired token
        token = PostPreviewToken.objects.create(
            post=self.post,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
            max_access_count=10
        )
        
        url = reverse('blog:post_preview_token', kwargs={'token': token.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preview Not Available')
        self.assertContains(response, 'expired or reached its usage limit')


class SchedulingIntegrationTests(TransactionTestCase):
    """
    Integration tests for the complete scheduling workflow.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_complete_scheduling_workflow(self):
        """Test the complete post scheduling workflow."""
        # 1. Create a draft post
        post = Post.objects.create(
            title='Draft Post',
            content='This will be scheduled for publication.',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        # 2. Schedule the post
        future_time = timezone.now() + timedelta(minutes=1)
        
        with patch('apps.blog.tasks.notify_author_post_published.delay') as mock_notify:
            schedule_post_publication(post.id, future_time.isoformat())
        
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.SCHEDULED)
        
        # 3. Simulate time passing and run publish task
        with patch('django.utils.timezone.now', return_value=future_time + timedelta(minutes=1)):
            with patch('apps.blog.tasks.notify_author_post_published.delay') as mock_notify:
                result = publish_scheduled_posts()
        
        # 4. Verify post was published
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertEqual(result['published_count'], 1)
        mock_notify.assert_called_once_with(post.id)
    
    def test_preview_token_workflow(self):
        """Test the complete preview token workflow."""
        # 1. Create a draft post
        post = Post.objects.create(
            title='Draft Post for Preview',
            content='This is a draft post that will be previewed.',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        # 2. Create preview token
        token = PostPreviewToken.create_token(
            post=post,
            created_by=self.user,
            expires_in_hours=1,
            max_access_count=3
        )
        
        # 3. Access preview multiple times
        for i in range(3):
            self.assertTrue(token.is_valid())
            token.increment_access_count()
        
        # 4. Token should be invalid after max uses
        self.assertFalse(token.is_valid())
        
        # 5. Test cleanup of expired tokens
        # Make token appear old
        token.created_at = timezone.now() - timedelta(hours=25)
        token.save()
        
        deleted_count = PostPreviewToken.cleanup_expired_tokens()
        self.assertEqual(deleted_count, 1)
        self.assertFalse(PostPreviewToken.objects.filter(id=token.id).exists())