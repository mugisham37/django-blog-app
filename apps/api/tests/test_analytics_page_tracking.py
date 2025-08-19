"""
Tests for analytics page view tracking system.
Tests the accuracy and performance of page view tracking functionality.
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from celery import current_app

from apps.analytics.models import PageView, SearchQuery
from apps.analytics.tasks import track_page_view, update_page_view_engagement, update_analytics
from apps.analytics.views import TrackPageViewView, TrackEngagementView, AnalyticsAPIView
from apps.analytics.signals import AnalyticsTrackingMixin
from apps.blog.models import Post, Category
from apps.accounts.models import Profile

User = get_user_model()


class PageViewModelTest(TestCase):
    """
    Test PageView model functionality and methods.
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
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_page_view_creation(self):
        """Test basic PageView creation."""
        page_view = PageView.objects.create(
            post=self.post,
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            referrer='https://example.com',
            session_key='test_session',
            path='/test-post/',
            query_string='utm_source=test'
        )
        
        self.assertEqual(page_view.post, self.post)
        self.assertEqual(page_view.user, self.user)
        self.assertEqual(page_view.ip_address, '192.168.1.1')
        self.assertEqual(page_view.path, '/test-post/')
        self.assertTrue(page_view.created_at)
    
    def test_page_view_without_post(self):
        """Test PageView creation for non-post pages."""
        page_view = PageView.objects.create(
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session',
            path='/about/',
        )
        
        self.assertIsNone(page_view.post)
        self.assertIsNone(page_view.user)
        self.assertEqual(page_view.path, '/about/')
    
    def test_engagement_score_calculation(self):
        """Test engagement score calculation."""
        # Test with no engagement data
        page_view = PageView.objects.create(
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session',
            path='/test/'
        )
        self.assertEqual(page_view.get_engagement_score(), 0)
        
        # Test with time on page only
        page_view.time_on_page = 120  # 2 minutes
        self.assertEqual(page_view.get_engagement_score(), 20)  # 120/6 = 20
        
        # Test with scroll depth only
        page_view.time_on_page = None
        page_view.scroll_depth = 80
        self.assertEqual(page_view.get_engagement_score(), 40)  # 80/2 = 40
        
        # Test with both metrics
        page_view.time_on_page = 180  # 3 minutes
        page_view.scroll_depth = 90
        expected_score = min(50, 180 // 6) + min(50, 90 // 2)  # 30 + 45 = 75
        self.assertEqual(page_view.get_engagement_score(), expected_score)
        
        # Test maximum scores
        page_view.time_on_page = 600  # 10 minutes (should cap at 50)
        page_view.scroll_depth = 100
        self.assertEqual(page_view.get_engagement_score(), 100)  # 50 + 50 = 100
    
    def test_page_view_manager_methods(self):
        """Test PageViewManager custom methods."""
        # Create test data
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Create page views for different time periods
        PageView.objects.create(
            post=self.post,
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='session1',
            path='/test-post/',
            created_at=now
        )
        
        PageView.objects.create(
            post=self.post,
            ip_address='192.168.1.2',
            user_agent='Test',
            session_key='session2',
            path='/test-post/',
            created_at=yesterday
        )
        
        # Test popular_posts method
        popular_posts = PageView.objects.popular_posts(limit=5, days=2)
        self.assertEqual(len(popular_posts), 1)
        self.assertEqual(popular_posts[0]['post__id'], self.post.id)
        self.assertEqual(popular_posts[0]['view_count'], 2)
        
        # Test with shorter time range
        popular_posts_1d = PageView.objects.popular_posts(limit=5, days=1)
        self.assertEqual(len(popular_posts_1d), 1)
        self.assertEqual(popular_posts_1d[0]['view_count'], 1)
    
    def test_traffic_by_referrer(self):
        """Test traffic_by_referrer method."""
        # Create page views with different referrers
        PageView.objects.create(
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='session1',
            path='/test/',
            referrer='https://google.com'
        )
        
        PageView.objects.create(
            ip_address='192.168.1.2',
            user_agent='Test',
            session_key='session2',
            path='/test/',
            referrer='https://google.com'
        )
        
        PageView.objects.create(
            ip_address='192.168.1.3',
            user_agent='Test',
            session_key='session3',
            path='/test/',
            referrer='https://facebook.com'
        )
        
        traffic_sources = PageView.objects.traffic_by_referrer(limit=10, days=1)
        self.assertEqual(len(traffic_sources), 2)
        
        # Should be ordered by visit count
        self.assertEqual(traffic_sources[0]['referrer'], 'https://google.com')
        self.assertEqual(traffic_sources[0]['visit_count'], 2)
        self.assertEqual(traffic_sources[1]['referrer'], 'https://facebook.com')
        self.assertEqual(traffic_sources[1]['visit_count'], 1)
    
    def test_daily_views(self):
        """Test daily_views method."""
        now = timezone.now()
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()
        
        # Create views for different days
        PageView.objects.create(
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='session1',
            path='/test/',
            created_at=now
        )
        
        PageView.objects.create(
            ip_address='192.168.1.2',
            user_agent='Test',
            session_key='session2',
            path='/test/',
            created_at=now - timedelta(days=1)
        )
        
        daily_views = PageView.objects.daily_views(days=2)
        self.assertEqual(len(daily_views), 2)
        
        # Check that data is properly aggregated by date
        dates_in_result = [item['date'] for item in daily_views]
        self.assertIn(today, dates_in_result)
        self.assertIn(yesterday, dates_in_result)


class PageViewTrackingTaskTest(TransactionTestCase):
    """
    Test Celery tasks for page view tracking.
    Uses TransactionTestCase for proper Celery testing.
    """
    
    def setUp(self):
        # Configure Celery for testing
        current_app.conf.task_always_eager = True
        current_app.conf.task_eager_propagates = True
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_track_page_view_task(self):
        """Test the track_page_view Celery task."""
        # Execute the task
        result = track_page_view.delay(
            post_id=self.post.id,
            user_id=self.user.id,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            referrer='https://example.com',
            session_key='test_session',
            path='/test-post/',
            query_string='utm_source=test'
        )
        
        # Check that task completed successfully
        self.assertTrue(result.successful())
        
        # Check that PageView was created
        page_view = PageView.objects.get(id=result.result)
        self.assertEqual(page_view.post, self.post)
        self.assertEqual(page_view.user, self.user)
        self.assertEqual(page_view.ip_address, '192.168.1.1')
        self.assertEqual(page_view.path, '/test-post/')
        
        # Check that post view count was incremented
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, 1)
    
    def test_track_page_view_without_post(self):
        """Test tracking page view for non-post pages."""
        result = track_page_view.delay(
            user_id=self.user.id,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session',
            path='/about/'
        )
        
        self.assertTrue(result.successful())
        
        page_view = PageView.objects.get(id=result.result)
        self.assertIsNone(page_view.post)
        self.assertEqual(page_view.user, self.user)
        self.assertEqual(page_view.path, '/about/')
    
    def test_track_page_view_anonymous_user(self):
        """Test tracking page view for anonymous users."""
        result = track_page_view.delay(
            post_id=self.post.id,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='anonymous_session',
            path='/test-post/'
        )
        
        self.assertTrue(result.successful())
        
        page_view = PageView.objects.get(id=result.result)
        self.assertEqual(page_view.post, self.post)
        self.assertIsNone(page_view.user)
        self.assertEqual(page_view.session_key, 'anonymous_session')
    
    def test_update_page_view_engagement_task(self):
        """Test the update_page_view_engagement Celery task."""
        # Create a page view first
        page_view = PageView.objects.create(
            post=self.post,
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='test_session',
            path='/test-post/'
        )
        
        # Update engagement metrics
        result = update_page_view_engagement.delay(
            page_view_id=page_view.id,
            time_on_page=120,
            scroll_depth=75
        )
        
        self.assertTrue(result.successful())
        
        # Check that engagement data was updated
        page_view.refresh_from_db()
        self.assertEqual(page_view.time_on_page, 120)
        self.assertEqual(page_view.scroll_depth, 75)
    
    def test_update_analytics_task(self):
        """Test the update_analytics periodic task."""
        # Create some test data
        PageView.objects.create(
            post=self.post,
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='session1',
            path='/test-post/',
            time_on_page=120,
            scroll_depth=80
        )
        
        # Clear cache first
        cache.clear()
        
        # Execute the task
        result = update_analytics.delay()
        self.assertTrue(result.successful())
        
        # Check that cache was populated
        popular_posts = cache.get('popular_posts:30')
        self.assertIsNotNone(popular_posts)
        
        engagement_stats = cache.get('engagement_stats:30')
        self.assertIsNotNone(engagement_stats)
        self.assertEqual(engagement_stats['total_engaged_views'], 1)
    
    @patch('apps.analytics.tasks.logger')
    def test_track_page_view_error_handling(self, mock_logger):
        """Test error handling in track_page_view task."""
        # Test with invalid post ID
        result = track_page_view.delay(
            post_id=99999,  # Non-existent post
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='test_session',
            path='/invalid-post/'
        )
        
        # Task should still complete but log a warning
        self.assertTrue(result.successful())
        mock_logger.warning.assert_called()
        
        # PageView should still be created without post
        page_view = PageView.objects.get(id=result.result)
        self.assertIsNone(page_view.post)


class PageViewTrackingViewTest(TestCase):
    """
    Test views for page view tracking API endpoints.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    @patch('apps.analytics.views.track_page_view.delay')
    def test_track_page_view_api(self, mock_task):
        """Test the TrackPageViewView API endpoint."""
        mock_task.return_value = Mock(id='test-task-id')
        
        data = {
            'post_id': self.post.id,
            'path': '/test-post/',
            'query_string': 'utm_source=test'
        }
        
        response = self.client.post(
            '/analytics/track/page-view/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='192.168.1.1',
            HTTP_USER_AGENT='Test User Agent',
            HTTP_REFERER='https://example.com'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['task_id'], 'test-task-id')
        
        # Check that task was called with correct parameters
        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]
        self.assertEqual(call_kwargs['post_id'], self.post.id)
        self.assertEqual(call_kwargs['path'], '/test-post/')
        self.assertEqual(call_kwargs['ip_address'], '192.168.1.1')
    
    def test_track_page_view_invalid_json(self):
        """Test API with invalid JSON data."""
        response = self.client.post(
            '/analytics/track/page-view/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
    
    @patch('apps.analytics.views.update_page_view_engagement.delay')
    def test_track_engagement_api(self, mock_task):
        """Test the TrackEngagementView API endpoint."""
        mock_task.return_value = Mock(id='test-task-id')
        
        # Create a page view first
        page_view = PageView.objects.create(
            post=self.post,
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='test_session',
            path='/test-post/'
        )
        
        data = {
            'page_view_id': page_view.id,
            'time_on_page': 120,
            'scroll_depth': 75
        }
        
        response = self.client.post(
            '/analytics/track/engagement/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that task was called
        mock_task.assert_called_once_with(
            page_view_id=page_view.id,
            time_on_page=120,
            scroll_depth=75
        )
    
    def test_analytics_api_permission_required(self):
        """Test that analytics API requires staff permissions."""
        response = self.client.get('/analytics/api/data/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login as regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/analytics/api/data/')
        self.assertEqual(response.status_code, 403)  # Permission denied
        
        # Make user staff
        self.user.is_staff = True
        self.user.save()
        
        response = self.client.get('/analytics/api/data/')
        self.assertEqual(response.status_code, 200)
    
    def test_analytics_api_overview(self):
        """Test analytics API overview endpoint."""
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Create some test data
        PageView.objects.create(
            post=self.post,
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test',
            session_key='session1',
            path='/test-post/',
            time_on_page=120,
            scroll_depth=80
        )
        
        response = self.client.get('/analytics/api/data/?metric=overview&days=30')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('total_views', data)
        self.assertIn('unique_visitors', data)
        self.assertIn('avg_time_on_page', data)
        self.assertEqual(data['total_views'], 1)
        self.assertEqual(data['unique_visitors'], 1)


class AnalyticsTrackingMixinTest(TestCase):
    """
    Test the AnalyticsTrackingMixin for automatic page view tracking.
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
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_get_client_ip(self):
        """Test IP address extraction from request."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        mixin = AnalyticsTrackingMixin()
        
        # Test with REMOTE_ADDR
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = mixin.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test with X-Forwarded-For
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        ip = mixin.get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')
    
    @patch('apps.analytics.signals.track_page_view.delay')
    def test_mixin_tracks_page_view(self, mock_task):
        """Test that mixin automatically tracks page views."""
        from django.test import RequestFactory
        from django.views.generic import DetailView
        
        # Create a test view with the mixin
        class TestView(AnalyticsTrackingMixin, DetailView):
            model = Post
            template_name = 'test.html'
            
            def get_object(self):
                return self.post
        
        factory = RequestFactory()
        request = factory.get('/test-post/')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test User Agent'
        
        view = TestView()
        view.post = self.post
        view.setup(request)
        
        # Mock the template rendering to avoid template not found error
        with patch.object(view, 'render_to_response') as mock_render:
            mock_render.return_value = Mock(status_code=200)
            response = view.dispatch(request)
        
        # Check that tracking task was called
        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]
        self.assertEqual(call_kwargs['post_id'], self.post.id)
        self.assertEqual(call_kwargs['user_id'], self.user.id)


class PageViewPerformanceTest(TestCase):
    """
    Test performance aspects of page view tracking.
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
        
        # Create multiple posts for testing
        self.posts = []
        for i in range(10):
            post = Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content=f'Test content {i}',
                author=self.user,
                category=self.category,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now()
            )
            self.posts.append(post)
    
    def test_bulk_page_view_creation_performance(self):
        """Test performance of creating multiple page views."""
        import time
        
        start_time = time.time()
        
        # Create 100 page views
        page_views = []
        for i in range(100):
            page_view = PageView(
                post=self.posts[i % len(self.posts)],
                user=self.user if i % 2 == 0 else None,
                ip_address=f'192.168.1.{i % 255}',
                user_agent='Test User Agent',
                session_key=f'session_{i}',
                path=f'/test-post-{i % len(self.posts)}/'
            )
            page_views.append(page_view)
        
        PageView.objects.bulk_create(page_views)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(creation_time, 1.0)
        
        # Verify all page views were created
        self.assertEqual(PageView.objects.count(), 100)
    
    def test_popular_posts_query_performance(self):
        """Test performance of popular posts query."""
        # Create page views for testing
        for i in range(50):
            PageView.objects.create(
                post=self.posts[i % len(self.posts)],
                ip_address=f'192.168.1.{i}',
                user_agent='Test',
                session_key=f'session_{i}',
                path=f'/test-post-{i % len(self.posts)}/'
            )
        
        import time
        start_time = time.time()
        
        # Execute popular posts query
        popular_posts = list(PageView.objects.popular_posts(limit=10, days=30))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly (less than 0.1 seconds)
        self.assertLess(query_time, 0.1)
        self.assertGreater(len(popular_posts), 0)
    
    def test_analytics_caching_effectiveness(self):
        """Test that analytics caching improves performance."""
        # Create test data
        for i in range(20):
            PageView.objects.create(
                post=self.posts[i % len(self.posts)],
                ip_address=f'192.168.1.{i}',
                user_agent='Test',
                session_key=f'session_{i}',
                path=f'/test-post-{i % len(self.posts)}/',
                time_on_page=120,
                scroll_depth=80
            )
        
        # Clear cache
        cache.clear()
        
        # First call (should hit database)
        import time
        start_time = time.time()
        popular_posts_1 = PageView.objects.popular_posts(limit=10, days=30)
        first_call_time = time.time() - start_time
        
        # Cache the result
        cache.set('popular_posts:30', list(popular_posts_1), timeout=300)
        
        # Second call (should hit cache)
        start_time = time.time()
        popular_posts_2 = cache.get('popular_posts:30')
        second_call_time = time.time() - start_time
        
        # Cache should be significantly faster
        self.assertLess(second_call_time, first_call_time / 2)
        self.assertEqual(len(popular_posts_2), len(list(popular_posts_1)))