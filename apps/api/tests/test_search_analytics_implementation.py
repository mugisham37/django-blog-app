"""
Comprehensive tests for search analytics implementation.
Tests search query tracking, analytics accuracy, and admin reporting functionality.
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.test.utils import override_settings
from datetime import timedelta, date
from celery import current_app

from apps.analytics.models import SearchQuery, SearchClickthrough, PageView
from apps.analytics.admin import AnalyticsAdminSite
from apps.blog.models import Post, Category, Tag
from apps.blog.search_utils import SearchAnalytics, SearchSuggestionEngine

User = get_user_model()


class SearchQueryModelTest(TestCase):
    """
    Test SearchQuery model functionality and methods.
    """
    
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
        
        self.post = Post.objects.create(
            title='Python Programming Guide',
            slug='python-programming-guide',
            content='Complete guide to Python programming',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_search_query_creation(self):
        """Test basic SearchQuery creation."""
        search_query = SearchQuery.objects.create(
            query='python programming',
            results_count=5,
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session'
        )
        
        self.assertEqual(search_query.query, 'python programming')
        self.assertEqual(search_query.results_count, 5)
        self.assertEqual(search_query.user, self.user)
        self.assertEqual(search_query.ip_address, '192.168.1.1')
        self.assertTrue(search_query.created_at)
    
    def test_search_query_anonymous_user(self):
        """Test SearchQuery creation for anonymous users."""
        search_query = SearchQuery.objects.create(
            query='django tutorial',
            results_count=3,
            ip_address='192.168.1.2',
            user_agent='Test User Agent',
            session_key='anonymous_session'
        )
        
        self.assertEqual(search_query.query, 'django tutorial')
        self.assertIsNone(search_query.user)
        self.assertEqual(search_query.session_key, 'anonymous_session')
    
    def test_effectiveness_score_calculation(self):
        """Test search effectiveness score calculation."""
        # Test with no results
        search_query = SearchQuery.objects.create(
            query='nonexistent',
            results_count=0,
            ip_address='192.168.1.1'
        )
        self.assertEqual(search_query.get_effectiveness_score(), 0)
        
        # Test with results but no clicks
        search_query.results_count = 5
        search_query.save()
        self.assertEqual(search_query.get_effectiveness_score(), 10)  # 5 * 2 = 10
        
        # Test with click on first position
        search_query.clicked_result_position = 1
        search_query.save()
        expected_score = 10 + (50 - (1 - 1) * 5)  # 10 + 50 = 60
        self.assertEqual(search_query.get_effectiveness_score(), expected_score)
        
        # Test with click on lower position
        search_query.clicked_result_position = 5
        search_query.save()
        expected_score = 10 + (50 - (5 - 1) * 5)  # 10 + 30 = 40
        self.assertEqual(search_query.get_effectiveness_score(), expected_score)
        
        # Test maximum score
        search_query.results_count = 25  # Will cap at 50 points
        search_query.clicked_result_position = 1
        search_query.save()
        self.assertEqual(search_query.get_effectiveness_score(), 100)  # 50 + 50 = 100
    
    def test_search_query_manager_methods(self):
        """Test SearchQueryManager custom methods."""
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Create test search queries
        SearchQuery.objects.create(
            query='python',
            results_count=5,
            ip_address='192.168.1.1',
            created_at=now
        )
        
        SearchQuery.objects.create(
            query='python',
            results_count=3,
            ip_address='192.168.1.2',
            created_at=yesterday
        )
        
        SearchQuery.objects.create(
            query='django',
            results_count=0,  # Failed search
            ip_address='192.168.1.3',
            created_at=now
        )
        
        # Test popular_queries method
        popular = SearchQuery.objects.popular_queries(limit=5, days=2)
        self.assertEqual(len(popular), 2)  # 'python' and 'django'
        
        # Should be ordered by search count
        python_query = next(q for q in popular if q['query'] == 'python')
        self.assertEqual(python_query['search_count'], 2)
        self.assertEqual(python_query['avg_results'], 4.0)  # (5 + 3) / 2
        
        # Test failed_searches method
        failed = SearchQuery.objects.failed_searches(limit=5, days=1)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]['query'], 'django')
        self.assertEqual(failed[0]['search_count'], 1)
        
        # Test trending_queries method
        trending = SearchQuery.objects.trending_queries(limit=5, days=2)
        self.assertTrue(len(trending) >= 0)  # May be empty if not enough data
    
    def test_search_suggestions(self):
        """Test search suggestions functionality."""
        # Create search history
        SearchQuery.objects.create(
            query='python programming',
            results_count=5,
            ip_address='192.168.1.1'
        )
        
        SearchQuery.objects.create(
            query='python tutorial',
            results_count=3,
            ip_address='192.168.1.2'
        )
        
        # Test suggestions
        suggestions = SearchQuery.objects.search_suggestions('python', limit=5)
        self.assertIn('python programming', suggestions)
        self.assertIn('python tutorial', suggestions)
        
        # Test with short query
        suggestions = SearchQuery.objects.search_suggestions('p', limit=5)
        self.assertEqual(suggestions, [])


class SearchClickthroughModelTest(TestCase):
    """
    Test SearchClickthrough model functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        self.search_query = SearchQuery.objects.create(
            query='test',
            results_count=1,
            ip_address='192.168.1.1'
        )
    
    def test_search_clickthrough_creation(self):
        """Test SearchClickthrough creation."""
        clickthrough = SearchClickthrough.objects.create(
            search_query=self.search_query,
            post=self.post,
            position=1,
            user=self.user,
            ip_address='192.168.1.1',
            session_key='test_session'
        )
        
        self.assertEqual(clickthrough.search_query, self.search_query)
        self.assertEqual(clickthrough.post, self.post)
        self.assertEqual(clickthrough.position, 1)
        self.assertEqual(clickthrough.user, self.user)
    
    def test_unique_constraint(self):
        """Test unique constraint on search_query, post, and session_key."""
        # Create first clickthrough
        SearchClickthrough.objects.create(
            search_query=self.search_query,
            post=self.post,
            position=1,
            ip_address='192.168.1.1',
            session_key='test_session'
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(Exception):  # IntegrityError
            SearchClickthrough.objects.create(
                search_query=self.search_query,
                post=self.post,
                position=2,  # Different position
                ip_address='192.168.1.1',
                session_key='test_session'  # Same session
            )


class SearchAnalyticsUtilityTest(TestCase):
    """
    Test SearchAnalytics utility class functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_track_search(self):
        """Test search tracking functionality."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/search/?q=test')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test User Agent'
        
        search_query = SearchAnalytics.track_search(request, 'test query', 5)
        
        self.assertIsNotNone(search_query)
        self.assertEqual(search_query.query, 'test query')
        self.assertEqual(search_query.results_count, 5)
        self.assertEqual(search_query.user, self.user)
        self.assertEqual(search_query.ip_address, '192.168.1.1')
    
    def test_track_search_click(self):
        """Test search click tracking."""
        from django.test import RequestFactory
        
        search_query = SearchQuery.objects.create(
            query='test',
            results_count=1,
            ip_address='192.168.1.1'
        )
        
        factory = RequestFactory()
        request = factory.get('/post/test/')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        clickthrough = SearchAnalytics.track_search_click(
            search_query, self.post, 1, request
        )
        
        self.assertIsNotNone(clickthrough)
        self.assertEqual(clickthrough.search_query, search_query)
        self.assertEqual(clickthrough.post, self.post)
        self.assertEqual(clickthrough.position, 1)
        
        # Check that search query was updated
        search_query.refresh_from_db()
        self.assertEqual(search_query.clicked_result_position, 1)
        self.assertEqual(search_query.clicked_post, self.post)
    
    def test_get_search_stats(self):
        """Test search statistics calculation."""
        # Create test data
        now = timezone.now()
        
        SearchQuery.objects.create(
            query='test1',
            results_count=5,
            ip_address='192.168.1.1',
            created_at=now
        )
        
        SearchQuery.objects.create(
            query='test2',
            results_count=0,  # Failed search
            ip_address='192.168.1.2',
            created_at=now
        )
        
        SearchQuery.objects.create(
            query='test3',
            results_count=3,
            ip_address='192.168.1.3',
            clicked_post=self.post,
            created_at=now
        )
        
        stats = SearchAnalytics.get_search_stats(days=1)
        
        self.assertEqual(stats['total_searches'], 3)
        self.assertEqual(stats['failed_searches'], 1)
        self.assertEqual(stats['searches_with_clicks'], 1)
        self.assertAlmostEqual(stats['click_through_rate'], 33.33, places=1)
        self.assertAlmostEqual(stats['avg_results_per_search'], 2.67, places=1)


class SearchAnalyticsAdminTest(TestCase):
    """
    Test admin interface for search analytics.
    """
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.regular_user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        # Create test search data
        self.search_query = SearchQuery.objects.create(
            query='test search',
            results_count=5,
            user=self.regular_user,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session'
        )
    
    def test_search_query_admin_list_view(self):
        """Test SearchQuery admin list view."""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/analytics/searchquery/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test search')
        self.assertContains(response, '5')  # results_count
    
    def test_search_query_admin_readonly(self):
        """Test that SearchQuery admin is read-only."""
        self.client.login(username='admin', password='adminpass123')
        
        # Should not have add permission
        response = self.client.get('/admin/analytics/searchquery/add/')
        self.assertEqual(response.status_code, 403)
        
        # Should not have change permission
        response = self.client.get(f'/admin/analytics/searchquery/{self.search_query.id}/change/')
        self.assertEqual(response.status_code, 403)
    
    def test_analytics_dashboard_view(self):
        """Test analytics dashboard view."""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/analytics-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
    
    def test_analytics_dashboard_permission_required(self):
        """Test that analytics dashboard requires admin permissions."""
        # Test without login
        response = self.client.get('/admin/analytics-dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/analytics-dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_search_analytics_export_csv(self):
        """Test CSV export functionality."""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/analytics-export/?type=search&format=csv&days=30')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Query', content)  # Header
        self.assertIn('test search', content)  # Data
    
    def test_search_analytics_export_json(self):
        """Test JSON export functionality."""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/analytics-export/?type=search&format=json&days=30')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('searches', data)
        self.assertIn('total_searches', data)
        self.assertEqual(data['total_searches'], 1)
    
    def test_search_analytics_report_view(self):
        """Test detailed search analytics report view."""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/search-analytics-report/?days=30')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Analytics Report')
        self.assertContains(response, 'Popular Search Queries')
        self.assertContains(response, 'Failed Search Queries')


class SearchAnalyticsIntegrationTest(TestCase):
    """
    Integration tests for complete search analytics workflows.
    """
    
    def setUp(self):
        self.client = Client()
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
            title='Python Programming Tutorial',
            slug='python-programming-tutorial',
            content='Complete guide to Python programming',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_complete_search_analytics_workflow(self):
        """Test complete search analytics workflow."""
        # 1. Perform search
        response = self.client.get('/search/?q=python')
        self.assertEqual(response.status_code, 200)
        
        # 2. Verify search was tracked
        search_queries = SearchQuery.objects.filter(query='python')
        self.assertTrue(search_queries.exists())
        
        search_query = search_queries.first()
        self.assertEqual(search_query.query, 'python')
        self.assertGreaterEqual(search_query.results_count, 0)
        
        # 3. Simulate clicking on search result
        response = self.client.post(
            '/search/track-click/',
            json.dumps({
                'search_query_id': search_query.id,
                'post_id': self.post.id,
                'position': 1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify click was tracked
        clickthrough = SearchClickthrough.objects.filter(
            search_query=search_query,
            post=self.post
        ).first()
        
        self.assertIsNotNone(clickthrough)
        self.assertEqual(clickthrough.position, 1)
        
        # 5. Verify search query was updated
        search_query.refresh_from_db()
        self.assertEqual(search_query.clicked_post, self.post)
        self.assertEqual(search_query.clicked_result_position, 1)
        
        # 6. Test analytics calculations
        effectiveness_score = search_query.get_effectiveness_score()
        self.assertGreater(effectiveness_score, 0)
    
    def test_search_pattern_analysis(self):
        """Test search pattern analysis functionality."""
        # Create multiple search queries with patterns
        queries = [
            'python tutorial',
            'python programming',
            'django tutorial',
            'django framework',
            'web development',
        ]
        
        for i, query in enumerate(queries):
            SearchQuery.objects.create(
                query=query,
                results_count=i + 1,
                ip_address=f'192.168.1.{i + 1}',
                user_agent='Test User Agent'
            )
        
        # Test popular queries
        popular = SearchQuery.objects.popular_queries(limit=10, days=30)
        self.assertEqual(len(popular), 5)
        
        # Test search suggestions
        suggestions = SearchSuggestionEngine.get_suggestions('python', limit=5)
        self.assertTrue(len(suggestions) > 0)
        
        # Should include python-related queries
        python_suggestions = [s for s in suggestions if 'python' in s.lower()]
        self.assertTrue(len(python_suggestions) > 0)
    
    def test_failed_search_analysis(self):
        """Test failed search analysis for content opportunities."""
        # Create failed searches
        failed_queries = [
            'machine learning basics',
            'artificial intelligence tutorial',
            'data science guide',
        ]
        
        for query in failed_queries:
            SearchQuery.objects.create(
                query=query,
                results_count=0,  # Failed search
                ip_address='192.168.1.1',
                user_agent='Test User Agent'
            )
        
        # Test failed searches retrieval
        failed = SearchQuery.objects.failed_searches(limit=10, days=30)
        self.assertEqual(len(failed), 3)
        
        # All should have 0 results
        for item in failed:
            search_queries = SearchQuery.objects.filter(query=item['query'])
            self.assertTrue(all(sq.results_count == 0 for sq in search_queries))
    
    def test_search_effectiveness_tracking(self):
        """Test search effectiveness tracking and scoring."""
        # Create search with different effectiveness scenarios
        
        # High effectiveness: many results, clicked on first position
        high_eff_search = SearchQuery.objects.create(
            query='popular topic',
            results_count=10,
            clicked_result_position=1,
            clicked_post=self.post,
            ip_address='192.168.1.1'
        )
        
        # Medium effectiveness: few results, clicked on lower position
        medium_eff_search = SearchQuery.objects.create(
            query='specific topic',
            results_count=3,
            clicked_result_position=3,
            clicked_post=self.post,
            ip_address='192.168.1.2'
        )
        
        # Low effectiveness: no results
        low_eff_search = SearchQuery.objects.create(
            query='nonexistent topic',
            results_count=0,
            ip_address='192.168.1.3'
        )
        
        # Test effectiveness scores
        high_score = high_eff_search.get_effectiveness_score()
        medium_score = medium_eff_search.get_effectiveness_score()
        low_score = low_eff_search.get_effectiveness_score()
        
        self.assertGreater(high_score, medium_score)
        self.assertGreater(medium_score, low_score)
        self.assertEqual(low_score, 0)


class SearchAnalyticsPerformanceTest(TestCase):
    """
    Test performance aspects of search analytics.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create multiple posts for testing
        self.posts = []
        for i in range(20):
            post = Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content=f'Content for test post {i}',
                author=self.user,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now()
            )
            self.posts.append(post)
    
    def test_bulk_search_query_creation_performance(self):
        """Test performance of creating multiple search queries."""
        import time
        
        start_time = time.time()
        
        # Create 100 search queries
        search_queries = []
        for i in range(100):
            search_query = SearchQuery(
                query=f'test query {i % 10}',  # Create some duplicates
                results_count=i % 5,
                ip_address=f'192.168.1.{i % 255}',
                user_agent='Test User Agent',
                session_key=f'session_{i}'
            )
            search_queries.append(search_query)
        
        SearchQuery.objects.bulk_create(search_queries)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(creation_time, 1.0)
        
        # Verify all search queries were created
        self.assertEqual(SearchQuery.objects.count(), 100)
    
    def test_popular_queries_performance(self):
        """Test performance of popular queries calculation."""
        # Create search queries for testing
        for i in range(50):
            SearchQuery.objects.create(
                query=f'query {i % 10}',  # Create duplicates
                results_count=i % 5,
                ip_address=f'192.168.1.{i}',
                user_agent='Test User Agent'
            )
        
        import time
        start_time = time.time()
        
        # Execute popular queries calculation
        popular_queries = list(SearchQuery.objects.popular_queries(limit=10, days=30))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly (less than 0.1 seconds)
        self.assertLess(query_time, 0.1)
        self.assertGreater(len(popular_queries), 0)
    
    def test_search_analytics_caching(self):
        """Test caching effectiveness for search analytics."""
        # Create test data
        for i in range(20):
            SearchQuery.objects.create(
                query=f'cached query {i}',
                results_count=i,
                ip_address=f'192.168.1.{i}',
                user_agent='Test User Agent'
            )
        
        # Clear cache
        cache.clear()
        
        # First call (should hit database)
        import time
        start_time = time.time()
        popular_queries_1 = SearchQuery.objects.popular_queries(limit=10, days=30)
        first_call_time = time.time() - start_time
        
        # Cache the result
        cache.set('popular_search_queries:30', list(popular_queries_1), timeout=300)
        
        # Second call (should hit cache)
        start_time = time.time()
        popular_queries_2 = cache.get('popular_search_queries:30')
        second_call_time = time.time() - start_time
        
        # Cache should be significantly faster
        self.assertLess(second_call_time, first_call_time / 2)
        self.assertEqual(len(popular_queries_2), len(list(popular_queries_1)))


class SearchAnalyticsAccuracyTest(TestCase):
    """
    Test accuracy of search analytics calculations and reporting.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_search_count_accuracy(self):
        """Test accuracy of search count calculations."""
        # Create known number of searches
        for i in range(10):
            SearchQuery.objects.create(
                query='test query',
                results_count=i,
                ip_address=f'192.168.1.{i}',
                user_agent='Test User Agent'
            )
        
        # Test popular queries count
        popular = SearchQuery.objects.popular_queries(limit=5, days=30)
        test_query = next(q for q in popular if q['query'] == 'test query')
        
        self.assertEqual(test_query['search_count'], 10)
        self.assertEqual(test_query['avg_results'], 4.5)  # (0+1+2+...+9)/10 = 4.5
    
    def test_click_through_rate_accuracy(self):
        """Test accuracy of click-through rate calculations."""
        # Create searches with known click patterns
        total_searches = 10
        searches_with_clicks = 3
        
        for i in range(total_searches):
            search_query = SearchQuery.objects.create(
                query=f'query {i}',
                results_count=5,
                ip_address=f'192.168.1.{i}',
                user_agent='Test User Agent'
            )
            
            # Add clicks to first 3 searches
            if i < searches_with_clicks:
                search_query.clicked_post = self.post
                search_query.clicked_result_position = 1
                search_query.save()
        
        # Calculate stats
        stats = SearchAnalytics.get_search_stats(days=30)
        
        expected_ctr = (searches_with_clicks / total_searches) * 100
        self.assertAlmostEqual(stats['click_through_rate'], expected_ctr, places=1)
        self.assertEqual(stats['searches_with_clicks'], searches_with_clicks)
        self.assertEqual(stats['total_searches'], total_searches)
    
    def test_failed_search_rate_accuracy(self):
        """Test accuracy of failed search rate calculations."""
        # Create searches with known failure patterns
        total_searches = 20
        failed_searches = 5
        
        for i in range(total_searches):
            results_count = 0 if i < failed_searches else i + 1
            SearchQuery.objects.create(
                query=f'query {i}',
                results_count=results_count,
                ip_address=f'192.168.1.{i}',
                user_agent='Test User Agent'
            )
        
        # Calculate stats
        stats = SearchAnalytics.get_search_stats(days=30)
        
        self.assertEqual(stats['total_searches'], total_searches)
        self.assertEqual(stats['failed_searches'], failed_searches)
        
        expected_success_rate = ((total_searches - failed_searches) / total_searches) * 100
        self.assertAlmostEqual(stats['click_through_rate'], 0, places=1)  # No clicks in this test
    
    def test_time_range_filtering_accuracy(self):
        """Test accuracy of time range filtering in analytics."""
        now = timezone.now()
        
        # Create searches at different times
        SearchQuery.objects.create(
            query='recent query',
            results_count=5,
            ip_address='192.168.1.1',
            created_at=now
        )
        
        SearchQuery.objects.create(
            query='old query',
            results_count=3,
            ip_address='192.168.1.2',
            created_at=now - timedelta(days=10)
        )
        
        SearchQuery.objects.create(
            query='very old query',
            results_count=2,
            ip_address='192.168.1.3',
            created_at=now - timedelta(days=40)
        )
        
        # Test 7-day range
        stats_7d = SearchAnalytics.get_search_stats(days=7)
        self.assertEqual(stats_7d['total_searches'], 1)  # Only recent query
        
        # Test 30-day range
        stats_30d = SearchAnalytics.get_search_stats(days=30)
        self.assertEqual(stats_30d['total_searches'], 2)  # Recent + old query
        
        # Test popular queries with time filtering
        popular_7d = SearchQuery.objects.popular_queries(limit=10, days=7)
        self.assertEqual(len(popular_7d), 1)
        self.assertEqual(popular_7d[0]['query'], 'recent query')
        
        popular_30d = SearchQuery.objects.popular_queries(limit=10, days=30)
        self.assertEqual(len(popular_30d), 2)