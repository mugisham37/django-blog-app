"""
Tests for analytics dashboard functionality and data export.
"""

import json
import csv
from io import StringIO, BytesIO
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from django.http import HttpResponse
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from apps.analytics.models import PageView, SearchQuery, SearchClickthrough
from apps.analytics.admin import AnalyticsAdminSite, AnalyticsDashboardWidget
from apps.analytics.consumers import AnalyticsDashboardConsumer, LiveStatsConsumer
from apps.analytics.tasks import send_realtime_analytics_update
from apps.blog.models import Post, Category
from apps.accounts.models import Profile

User = get_user_model()


class AnalyticsDashboardTestCase(TestCase):
    """
    Test case for analytics dashboard functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create test blog content
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.admin_user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        # Create test analytics data
        self.create_test_analytics_data()
        
        self.client = Client()
        self.admin_site = AnalyticsAdminSite()
    
    def create_test_analytics_data(self):
        """Create test analytics data."""
        now = timezone.now()
        
        # Create page views
        for i in range(50):
            PageView.objects.create(
                post=self.post if i % 2 == 0 else None,
                user=self.regular_user if i % 3 == 0 else None,
                ip_address=f'192.168.1.{i % 255}',
                user_agent='Test User Agent',
                referrer='https://google.com' if i % 4 == 0 else '',
                session_key=f'session_{i}',
                path=f'/test-path-{i}/',
                time_on_page=60 + (i * 10) if i % 5 == 0 else None,
                scroll_depth=50 + (i % 50) if i % 5 == 0 else None,
                created_at=now - timedelta(hours=i)
            )
        
        # Create search queries
        search_terms = [
            'django tutorial', 'python programming', 'web development',
            'database design', 'api development', 'testing', 'deployment'
        ]
        
        for i, term in enumerate(search_terms * 5):
            SearchQuery.objects.create(
                query=f'{term} {i}' if i > 10 else term,
                results_count=10 - (i % 11),
                user=self.regular_user if i % 4 == 0 else None,
                ip_address=f'192.168.1.{i % 255}',
                user_agent='Test User Agent',
                session_key=f'search_session_{i}',
                clicked_post=self.post if i % 6 == 0 and (10 - (i % 11)) > 0 else None,
                clicked_result_position=1 if i % 6 == 0 and (10 - (i % 11)) > 0 else None,
                created_at=now - timedelta(hours=i)
            )
    
    def test_dashboard_widget_popular_posts(self):
        """Test popular posts widget functionality."""
        widget_data = AnalyticsDashboardWidget.get_popular_posts_widget()
        
        self.assertIn('title', widget_data)
        self.assertIn('posts', widget_data)
        self.assertEqual(widget_data['title'], 'Popular Posts (Last 7 Days)')
        self.assertIsInstance(widget_data['posts'], list)
    
    def test_dashboard_widget_traffic_stats(self):
        """Test traffic statistics widget functionality."""
        widget_data = AnalyticsDashboardWidget.get_traffic_stats_widget()
        
        self.assertIn('title', widget_data)
        self.assertIn('views', widget_data)
        self.assertIn('unique_visitors', widget_data)
        self.assertIn('searches', widget_data)
        self.assertIn('top_referrers', widget_data)
        
        # Check data structure
        self.assertIn('24h', widget_data['views'])
        self.assertIn('7d', widget_data['views'])
        self.assertIn('30d', widget_data['views'])
        
        self.assertIsInstance(widget_data['views']['24h'], int)
        self.assertIsInstance(widget_data['unique_visitors']['24h'], int)
        self.assertIsInstance(widget_data['searches']['24h'], int)
    
    def test_dashboard_widget_engagement(self):
        """Test engagement widget functionality."""
        widget_data = AnalyticsDashboardWidget.get_engagement_widget()
        
        self.assertIn('title', widget_data)
        self.assertIn('avg_time_on_page', widget_data)
        self.assertIn('avg_scroll_depth', widget_data)
        self.assertIn('engaged_sessions', widget_data)
        self.assertIn('total_views', widget_data)
        self.assertIn('engagement_rate', widget_data)
        
        self.assertIsInstance(widget_data['avg_time_on_page'], (int, float))
        self.assertIsInstance(widget_data['avg_scroll_depth'], (int, float))
        self.assertIsInstance(widget_data['engaged_sessions'], int)
        self.assertIsInstance(widget_data['engagement_rate'], (int, float))
    
    def test_dashboard_view_access_control(self):
        """Test dashboard view access control."""
        dashboard_url = '/admin/analytics-dashboard/'
        
        # Test unauthenticated access
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test regular user access
        self.client.login(username='user', password='testpass123')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test staff user access
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        # Test admin user access
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_view_context(self):
        """Test dashboard view context data."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/analytics-dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('popular_posts', response.context)
        self.assertIn('traffic_stats', response.context)
        self.assertIn('engagement_stats', response.context)
        self.assertIn('search_stats', response.context)
        self.assertIn('recent_searches', response.context)
    
    def test_search_analytics_report_view(self):
        """Test search analytics report view."""
        self.client.login(username='admin', password='testpass123')
        
        # Test default report
        response = self.client.get('/admin/search-analytics-report/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('search_stats', response.context)
        self.assertIn('popular_queries', response.context)
        self.assertIn('failed_queries', response.context)
        
        # Test with custom days parameter
        response = self.client.get('/admin/search-analytics-report/?days=7')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 7)
        
        # Test with invalid days parameter
        response = self.client.get('/admin/search-analytics-report/?days=500')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 365)  # Should be capped at 365
    
    def test_analytics_caching(self):
        """Test analytics data caching."""
        # Clear cache
        cache.clear()
        
        # First call should hit database
        with self.assertNumQueries(4):  # Expected number of queries
            widget_data = AnalyticsDashboardWidget.get_popular_posts_widget()
        
        # Second call should use cache
        with self.assertNumQueries(0):
            cached_data = AnalyticsDashboardWidget.get_popular_posts_widget()
        
        self.assertEqual(widget_data, cached_data)


class AnalyticsExportTestCase(TestCase):
    """
    Test case for analytics data export functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test data
        self.create_test_data()
        
        self.client = Client()
        self.admin_site = AnalyticsAdminSite()
    
    def create_test_data(self):
        """Create test data for export testing."""
        now = timezone.now()
        
        # Create test post
        category = Category.objects.create(name='Test', slug='test')
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.admin_user,
            category=category,
            status=Post.Status.PUBLISHED,
            published_at=now
        )
        
        # Create search queries
        for i in range(10):
            SearchQuery.objects.create(
                query=f'test query {i}',
                results_count=i,
                user=self.admin_user if i % 2 == 0 else None,
                ip_address=f'192.168.1.{i}',
                user_agent='Test Agent',
                session_key=f'session_{i}',
                clicked_post=post if i > 5 else None,
                clicked_result_position=1 if i > 5 else None,
                created_at=now - timedelta(hours=i)
            )
        
        # Create page views
        for i in range(15):
            PageView.objects.create(
                post=post if i % 3 == 0 else None,
                user=self.admin_user if i % 4 == 0 else None,
                ip_address=f'192.168.1.{i}',
                user_agent='Test Agent',
                referrer='https://example.com' if i % 5 == 0 else '',
                session_key=f'session_{i}',
                path=f'/path/{i}/',
                time_on_page=60 + i if i % 3 == 0 else None,
                scroll_depth=50 + i if i % 3 == 0 else None,
                created_at=now - timedelta(hours=i)
            )
    
    def test_csv_export_search_analytics(self):
        """Test CSV export of search analytics."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/admin/analytics-export/?type=search&format=csv&days=30')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('search_analytics_30days.csv', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Search Analytics Export', content)
        self.assertIn('Total Searches', content)
        self.assertIn('Success Rate', content)
    
    def test_json_export_search_analytics(self):
        """Test JSON export of search analytics."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/admin/analytics-export/?type=search&format=json&days=30')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Parse JSON content
        data = json.loads(response.content)
        self.assertIn('period_days', data)
        self.assertIn('total_searches', data)
        self.assertIn('searches', data)
        self.assertEqual(data['period_days'], 30)
        self.assertIsInstance(data['searches'], list)
    
    def test_csv_export_pageviews(self):
        """Test CSV export of page views."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/admin/analytics-export/?type=pageviews&format=csv&days=30')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('pageviews_30days.csv', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(StringIO(content))
        headers = next(csv_reader)
        
        expected_headers = [
            'Path', 'Post Title', 'User', 'IP Address', 'Referrer',
            'Time on Page', 'Scroll Depth', 'Created At'
        ]
        self.assertEqual(headers, expected_headers)
    
    @patch('openpyxl.Workbook')
    def test_excel_export_search_analytics(self, mock_workbook):
        """Test Excel export of search analytics."""
        # Mock Excel workbook
        mock_wb = MagicMock()
        mock_workbook.return_value = mock_wb
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_wb.create_sheet.return_value = mock_ws
        
        # Mock BytesIO save
        mock_output = BytesIO()
        mock_wb.save.return_value = None
        
        self.client.login(username='admin', password='testpass123')
        
        with patch('io.BytesIO', return_value=mock_output):
            response = self.client.get('/admin/analytics-export/?type=search&format=excel&days=30')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('search_analytics_30days.xlsx', response['Content-Disposition'])
    
    def test_export_access_control(self):
        """Test export functionality access control."""
        export_url = '/admin/analytics-export/?type=search&format=csv'
        
        # Test unauthenticated access
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 302)
        
        # Test regular user access
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 302)
        
        # Test admin access
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_export_parameters(self):
        """Test handling of invalid export parameters."""
        self.client.login(username='admin', password='testpass123')
        
        # Invalid export type
        response = self.client.get('/admin/analytics-export/?type=invalid&format=csv')
        self.assertEqual(response.status_code, 400)
        
        # Invalid format
        response = self.client.get('/admin/analytics-export/?type=search&format=invalid')
        self.assertEqual(response.status_code, 400)


class WebSocketAnalyticsTestCase(TestCase):
    """
    Test case for WebSocket real-time analytics functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
    
    async def test_analytics_dashboard_consumer_connection(self):
        """Test WebSocket connection for analytics dashboard."""
        # Test staff user connection
        communicator = WebsocketCommunicator(
            AnalyticsDashboardConsumer.as_asgi(),
            "/ws/analytics/dashboard/"
        )
        communicator.scope['user'] = self.admin_user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive initial dashboard update
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'dashboard_update')
        self.assertIn('data', response)
        
        await communicator.disconnect()
    
    async def test_analytics_dashboard_consumer_access_control(self):
        """Test WebSocket access control."""
        # Test regular user connection (should be rejected)
        communicator = WebsocketCommunicator(
            AnalyticsDashboardConsumer.as_asgi(),
            "/ws/analytics/dashboard/"
        )
        communicator.scope['user'] = self.regular_user
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
    
    async def test_analytics_dashboard_consumer_messages(self):
        """Test WebSocket message handling."""
        communicator = WebsocketCommunicator(
            AnalyticsDashboardConsumer.as_asgi(),
            "/ws/analytics/dashboard/"
        )
        communicator.scope['user'] = self.admin_user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial update
        await communicator.receive_json_from()
        
        # Test request update message
        await communicator.send_json_to({
            'type': 'request_update'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'dashboard_update')
        
        # Test change period message
        await communicator.send_json_to({
            'type': 'change_period',
            'period': 14
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'dashboard_update')
        self.assertEqual(response['data']['period'], 14)
        
        await communicator.disconnect()
    
    async def test_live_stats_consumer(self):
        """Test live stats WebSocket consumer."""
        communicator = WebsocketCommunicator(
            LiveStatsConsumer.as_asgi(),
            "/ws/analytics/live-stats/"
        )
        communicator.scope['user'] = self.admin_user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive initial live stats
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'live_stats')
        self.assertIn('data', response)
        
        # Test request stats message
        await communicator.send_json_to({
            'type': 'request_stats'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'live_stats')
        
        await communicator.disconnect()


class AnalyticsTasksTestCase(TestCase):
    """
    Test case for analytics background tasks.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create test analytics data
        now = timezone.now()
        for i in range(5):
            PageView.objects.create(
                user=self.user if i % 2 == 0 else None,
                ip_address=f'192.168.1.{i}',
                user_agent='Test Agent',
                session_key=f'session_{i}',
                path=f'/path/{i}/',
                created_at=now - timedelta(hours=i)
            )
            
            SearchQuery.objects.create(
                query=f'test query {i}',
                results_count=i,
                user=self.user if i % 2 == 0 else None,
                ip_address=f'192.168.1.{i}',
                user_agent='Test Agent',
                session_key=f'session_{i}',
                created_at=now - timedelta(hours=i)
            )
    
    @patch('apps.analytics.tasks.async_to_sync')
    @patch('apps.analytics.tasks.get_channel_layer')
    def test_send_realtime_analytics_update(self, mock_get_channel_layer, mock_async_to_sync):
        """Test real-time analytics update task."""
        # Mock channel layer
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Mock async_to_sync
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send
        
        # Execute task
        result = send_realtime_analytics_update()
        
        self.assertTrue(result)
        
        # Verify channel layer was called
        self.assertTrue(mock_get_channel_layer.called)
        self.assertTrue(mock_async_to_sync.called)
    
    def test_analytics_data_aggregation(self):
        """Test analytics data aggregation methods."""
        # Test popular posts aggregation
        popular_posts = PageView.objects.popular_posts(limit=5, days=7)
        self.assertIsInstance(popular_posts, list)
        
        # Test traffic by referrer
        traffic_sources = PageView.objects.traffic_by_referrer(limit=5, days=7)
        self.assertIsInstance(traffic_sources, list)
        
        # Test daily views
        daily_views = PageView.objects.daily_views(days=7)
        self.assertIsInstance(daily_views, list)
        
        # Test popular search queries
        from apps.analytics.admin import AnalyticsAdminSite
        admin_site = AnalyticsAdminSite()
        popular_queries = admin_site.get_popular_search_queries(days=7, limit=5)
        self.assertIsInstance(popular_queries, list)


class AnalyticsIntegrationTestCase(TestCase):
    """
    Integration tests for analytics dashboard functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.client = Client()
        
        # Create comprehensive test data
        self.create_comprehensive_test_data()
    
    def create_comprehensive_test_data(self):
        """Create comprehensive test data for integration testing."""
        now = timezone.now()
        
        # Create blog content
        category = Category.objects.create(name='Tech', slug='tech')
        
        posts = []
        for i in range(5):
            post = Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content=f'Content for post {i}',
                author=self.admin_user,
                category=category,
                status=Post.Status.PUBLISHED,
                published_at=now - timedelta(days=i)
            )
            posts.append(post)
        
        # Create varied analytics data
        search_terms = [
            'django', 'python', 'web development', 'api', 'database',
            'testing', 'deployment', 'security', 'performance'
        ]
        
        # Create search queries with realistic patterns
        for i, term in enumerate(search_terms * 3):
            results_count = max(0, 15 - (i % 16))  # Some searches fail
            SearchQuery.objects.create(
                query=term,
                results_count=results_count,
                user=self.admin_user if i % 5 == 0 else None,
                ip_address=f'192.168.{i % 255}.{(i * 7) % 255}',
                user_agent='Mozilla/5.0 Test Browser',
                session_key=f'session_{i}',
                clicked_post=posts[i % len(posts)] if results_count > 0 and i % 4 == 0 else None,
                clicked_result_position=1 if results_count > 0 and i % 4 == 0 else None,
                created_at=now - timedelta(hours=i, minutes=i * 5)
            )
        
        # Create page views with engagement data
        for i in range(100):
            post = posts[i % len(posts)] if i % 3 == 0 else None
            PageView.objects.create(
                post=post,
                user=self.admin_user if i % 7 == 0 else None,
                ip_address=f'192.168.{i % 255}.{(i * 3) % 255}',
                user_agent='Mozilla/5.0 Test Browser',
                referrer='https://google.com' if i % 6 == 0 else (
                    'https://twitter.com' if i % 8 == 0 else ''
                ),
                session_key=f'page_session_{i}',
                path=f'/post/{post.slug}/' if post else f'/page/{i}/',
                time_on_page=30 + (i * 5) % 300 if i % 4 == 0 else None,
                scroll_depth=25 + (i * 3) % 75 if i % 4 == 0 else None,
                created_at=now - timedelta(hours=i // 4, minutes=i * 2)
            )
    
    def test_full_dashboard_workflow(self):
        """Test complete dashboard workflow."""
        self.client.login(username='admin', password='testpass123')
        
        # Test dashboard access
        response = self.client.get('/admin/analytics-dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Verify all widgets are present
        self.assertContains(response, 'Popular Posts')
        self.assertContains(response, 'Traffic Statistics')
        self.assertContains(response, 'User Engagement')
        self.assertContains(response, 'Search Analytics')
        
        # Test search analytics report
        response = self.client.get('/admin/search-analytics-report/?days=30')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Analytics Report')
        
        # Test data exports
        response = self.client.get('/admin/analytics-export/?type=search&format=csv&days=30')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin/analytics-export/?type=pageviews&format=csv&days=30')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin/analytics-export/?type=search&format=json&days=30')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_performance(self):
        """Test dashboard performance with realistic data volumes."""
        self.client.login(username='admin', password='testpass123')
        
        # Test dashboard load time
        import time
        start_time = time.time()
        response = self.client.get('/admin/analytics-dashboard/')
        load_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0)  # Should load in under 2 seconds
        
        # Test export performance
        start_time = time.time()
        response = self.client.get('/admin/analytics-export/?type=search&format=csv&days=30')
        export_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(export_time, 5.0)  # Should export in under 5 seconds
    
    def test_dashboard_data_accuracy(self):
        """Test accuracy of dashboard data calculations."""
        self.client.login(username='admin', password='testpass123')
        
        # Get dashboard data
        response = self.client.get('/admin/analytics-dashboard/')
        
        # Verify data accuracy by comparing with direct database queries
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        actual_views_24h = PageView.objects.filter(created_at__gte=last_24h).count()
        actual_searches_24h = SearchQuery.objects.filter(created_at__gte=last_24h).count()
        
        # The response should contain these values
        self.assertContains(response, str(actual_views_24h))
        self.assertContains(response, str(actual_searches_24h))
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()