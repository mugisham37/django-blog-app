"""
Comprehensive tests for search functionality.
Tests search highlighting, suggestions, analytics, and performance.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test.utils import override_settings
from django.db import connection
from django.test import Client
from unittest.mock import patch, MagicMock

from apps.blog.models import Post, Category, Tag
from apps.analytics.models import SearchQuery, PageView, SearchClickthrough
from apps.blog.search_utils import (
    SearchHighlighter, SearchSuggestionEngine, SearchAnalytics, AdvancedSearchEngine
)

User = get_user_model()


class SearchHighlighterTestCase(TestCase):
    """
    Test cases for SearchHighlighter utility.
    """
    
    def setUp(self):
        self.highlighter = SearchHighlighter("python django")
    
    def test_extract_search_terms(self):
        """Test extraction of search terms from query."""
        # Test simple terms
        highlighter = SearchHighlighter("python django")
        self.assertEqual(set(highlighter.terms), {"python", "django"})
        
        # Test quoted phrases
        highlighter = SearchHighlighter('"machine learning" python')
        self.assertEqual(set(highlighter.terms), {"machine learning", "python"})
        
        # Test empty query
        highlighter = SearchHighlighter("")
        self.assertEqual(highlighter.terms, [])
        
        # Test single character terms (should be filtered out)
        highlighter = SearchHighlighter("a python b")
        self.assertEqual(highlighter.terms, ["python"])
    
    def test_highlight_text(self):
        """Test text highlighting functionality."""
        text = "Python is a great programming language for Django development"
        highlighted = self.highlighter.highlight_text(text)
        
        self.assertIn('<mark class="search-highlight">Python</mark>', highlighted)
        self.assertIn('<mark class="search-highlight">Django</mark>', highlighted)
    
    def test_highlight_text_case_insensitive(self):
        """Test case-insensitive highlighting."""
        text = "PYTHON and django are great"
        highlighted = self.highlighter.highlight_text(text)
        
        self.assertIn('<mark class="search-highlight">PYTHON</mark>', highlighted)
        self.assertIn('<mark class="search-highlight">django</mark>', highlighted)
    
    def test_highlight_text_with_max_length(self):
        """Test text highlighting with length limit."""
        text = "Python is a great programming language for Django development and web applications"
        highlighted = self.highlighter.highlight_text(text, max_length=50)
        
        self.assertTrue(len(highlighted) <= 60)  # Account for HTML tags
        self.assertIn('...', highlighted)
    
    def test_generate_snippet(self):
        """Test snippet generation around search terms."""
        text = "This is a long article about Python programming. Python is used for web development with Django framework. Django makes it easy to build web applications."
        snippet = self.highlighter.generate_snippet(text, snippet_length=100)
        
        # Should contain highlighted terms
        self.assertIn('<mark class="search-highlight">Python</mark>', snippet)
        self.assertIn('<mark class="search-highlight">Django</mark>', snippet)
        
        # Should be around the specified length
        self.assertTrue(len(snippet) <= 150)  # Account for HTML tags
    
    def test_generate_snippet_no_terms_found(self):
        """Test snippet generation when no terms are found."""
        highlighter = SearchHighlighter("nonexistent")
        text = "This is a text without the search terms."
        snippet = highlighter.generate_snippet(text, snippet_length=50)
        
        self.assertEqual(snippet, text[:50])
    
    def test_html_stripping(self):
        """Test that HTML tags are stripped before highlighting."""
        text = "<p>Python is <strong>great</strong> for Django</p>"
        highlighted = self.highlighter.highlight_text(text)
        
        # Should not contain original HTML tags
        self.assertNotIn('<p>', highlighted)
        self.assertNotIn('<strong>', highlighted)
        
        # Should contain highlighting
        self.assertIn('<mark class="search-highlight">Python</mark>', highlighted)


class SearchSuggestionEngineTestCase(TestCase):
    """
    Test cases for SearchSuggestionEngine.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.category = Category.objects.create(
            name='Programming',
            slug='programming'
        )
        
        self.tag1 = Tag.objects.create(name='Python', slug='python')
        self.tag2 = Tag.objects.create(name='Django', slug='django')
        
        self.post = Post.objects.create(
            title='Python Django Tutorial',
            content='Learn Python and Django web development',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        self.post.tags.add(self.tag1, self.tag2)
        
        # Create search history
        SearchQuery.objects.create(
            query='python tutorial',
            results_count=5,
            ip_address='127.0.0.1'
        )
        SearchQuery.objects.create(
            query='django framework',
            results_count=3,
            ip_address='127.0.0.1'
        )
    
    def test_get_suggestions_from_history(self):
        """Test getting suggestions from search history."""
        suggestions = SearchSuggestionEngine.get_suggestions('python', limit=5)
        self.assertIn('python tutorial', suggestions)
    
    def test_get_suggestions_from_content(self):
        """Test getting suggestions from post titles and tags."""
        suggestions = SearchSuggestionEngine.get_suggestions('django', limit=5)
        # Should include suggestions from post titles and tags
        self.assertTrue(len(suggestions) > 0)
    
    def test_get_suggestions_short_query(self):
        """Test that short queries return empty suggestions."""
        suggestions = SearchSuggestionEngine.get_suggestions('p', limit=5)
        self.assertEqual(suggestions, [])
    
    def test_get_trending_searches(self):
        """Test getting trending searches."""
        trending = SearchSuggestionEngine.get_trending_searches(limit=5)
        self.assertIsInstance(trending, list)
    
    def test_get_popular_searches(self):
        """Test getting popular searches."""
        popular = SearchSuggestionEngine.get_popular_searches(limit=5)
        self.assertIsInstance(popular, list)


class SearchAnalyticsTestCase(TestCase):
    """
    Test cases for SearchAnalytics utility.
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
        
        search_query = SearchAnalytics.track_search(request, 'test query', 5)
        
        self.assertIsNotNone(search_query)
        self.assertEqual(search_query.query, 'test query')
        self.assertEqual(search_query.results_count, 5)
        self.assertEqual(search_query.user, self.user)
    
    def test_track_search_anonymous_user(self):
        """Test search tracking for anonymous users."""
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/search/?q=test')
        request.user = AnonymousUser()
        request.session = {'session_key': 'test_session'}
        
        search_query = SearchAnalytics.track_search(request, 'test query', 3)
        
        self.assertIsNotNone(search_query)
        self.assertIsNone(search_query.user)
        self.assertEqual(search_query.results_count, 3)
    
    def test_track_search_click(self):
        """Test search click tracking."""
        from django.test import RequestFactory
        
        # Create a search query first
        search_query = SearchQuery.objects.create(
            query='test',
            results_count=1,
            ip_address='127.0.0.1'
        )
        
        factory = RequestFactory()
        request = factory.get('/post/test/')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        
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
        SearchQuery.objects.create(
            query='test1',
            results_count=5,
            ip_address='127.0.0.1'
        )
        SearchQuery.objects.create(
            query='test2',
            results_count=0,  # Failed search
            ip_address='127.0.0.1'
        )
        SearchQuery.objects.create(
            query='test3',
            results_count=3,
            ip_address='127.0.0.1',
            clicked_post=self.post
        )
        
        stats = SearchAnalytics.get_search_stats(days=30)
        
        self.assertEqual(stats['total_searches'], 3)
        self.assertEqual(stats['failed_searches'], 1)
        self.assertEqual(stats['searches_with_clicks'], 1)
        self.assertAlmostEqual(stats['click_through_rate'], 33.33, places=1)


class AdvancedSearchEngineTestCase(TestCase):
    """
    Test cases for AdvancedSearchEngine.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            slug='programming'
        )
        
        self.tag = Tag.objects.create(name='Python', slug='python')
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='Python Programming Tutorial',
            content='Learn Python programming from scratch',
            excerpt='A comprehensive Python tutorial',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        self.post1.tags.add(self.tag)
        
        self.post2 = Post.objects.create(
            title='Django Web Development',
            content='Build web applications with Django framework',
            excerpt='Django tutorial for beginners',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    })
    def test_search_posts_basic(self):
        """Test basic post search functionality."""
        # Note: This test uses SQLite which doesn't support PostgreSQL full-text search
        # In a real environment with PostgreSQL, this would test the full functionality
        
        results, snippets = AdvancedSearchEngine.search_posts('Python')
        
        # Should find posts containing 'Python'
        self.assertTrue(len(snippets) > 0)
        
        # Check that snippets contain highlighted content
        for snippet_data in snippets:
            self.assertIn('post', snippet_data)
            self.assertIn('highlighted_title', snippet_data)
            self.assertIn('snippet', snippet_data)
    
    def test_search_posts_with_filters(self):
        """Test search with additional filters."""
        filters = {
            'category': 'programming',
            'author': 'testuser'
        }
        
        results, snippets = AdvancedSearchEngine.search_posts('Python', filters)
        
        # All results should match the filters
        for snippet_data in snippets:
            post = snippet_data['post']
            self.assertEqual(post.category.slug, 'programming')
            self.assertEqual(post.author.username, 'testuser')
    
    def test_get_search_facets(self):
        """Test search facets generation."""
        facets = AdvancedSearchEngine.get_search_facets('Python')
        
        self.assertIn('categories', facets)
        self.assertIn('tags', facets)
        self.assertIn('authors', facets)
        self.assertIn('years', facets)
        
        # Should contain our test data
        if facets['categories']:
            category_names = [cat['name'] for cat in facets['categories']]
            self.assertIn('Programming', category_names)


class SearchViewsTestCase(TestCase):
    """
    Test cases for search views and API endpoints.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content for searching',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_search_view_get(self):
        """Test search view with GET request."""
        response = self.client.get(reverse('blog:search'), {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Results')
        self.assertIn('search_form', response.context)
        self.assertIn('query', response.context)
    
    def test_search_view_empty_query(self):
        """Test search view with empty query."""
        response = self.client.get(reverse('blog:search'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Our Blog')
    
    def test_search_suggestions_api(self):
        """Test search suggestions API endpoint."""
        # Create search history
        SearchQuery.objects.create(
            query='test query',
            results_count=1,
            ip_address='127.0.0.1'
        )
        
        response = self.client.get(
            reverse('blog:search_suggestions_api'),
            {'q': 'test', 'limit': 5}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        self.assertIn('query', data)
    
    def test_search_suggestions_api_short_query(self):
        """Test search suggestions API with short query."""
        response = self.client.get(
            reverse('blog:search_suggestions_api'),
            {'q': 'a'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['suggestions'], [])
    
    def test_track_search_click_api(self):
        """Test search click tracking API."""
        search_query = SearchQuery.objects.create(
            query='test',
            results_count=1,
            ip_address='127.0.0.1'
        )
        
        response = self.client.post(
            reverse('blog:track_search_click_api'),
            json.dumps({
                'search_query_id': search_query.id,
                'post_id': self.post.id,
                'position': 1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check that clickthrough was created
        self.assertTrue(
            SearchClickthrough.objects.filter(
                search_query=search_query,
                post=self.post
            ).exists()
        )
    
    def test_quick_search_api(self):
        """Test quick search API endpoint."""
        response = self.client.get(
            reverse('blog:quick_search_api'),
            {'q': 'test', 'limit': 5}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIn('query', data)
        self.assertIn('count', data)
    
    def test_search_analytics_view_staff_required(self):
        """Test that search analytics view requires staff permission."""
        response = self.client.get(reverse('blog:search_analytics'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Login as regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('blog:search_analytics'))
        
        # Should still redirect (not staff)
        self.assertEqual(response.status_code, 302)
        
        # Make user staff
        self.user.is_staff = True
        self.user.save()
        
        response = self.client.get(reverse('blog:search_analytics'))
        self.assertEqual(response.status_code, 200)


class SearchPerformanceTestCase(TransactionTestCase):
    """
    Test cases for search performance and optimization.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create multiple posts for performance testing
        self.posts = []
        for i in range(50):
            post = Post.objects.create(
                title=f'Test Post {i}',
                content=f'Content for test post {i} with various keywords',
                author=self.user,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now()
            )
            self.posts.append(post)
    
    def test_search_query_count(self):
        """Test that search doesn't generate excessive database queries."""
        with self.assertNumQueries(10):  # Adjust based on actual optimization
            results, snippets = AdvancedSearchEngine.search_posts('test')
            # Force evaluation of queryset
            list(results[:10])
    
    def test_search_response_time(self):
        """Test search response time performance."""
        import time
        
        start_time = time.time()
        results, snippets = AdvancedSearchEngine.search_posts('test')
        list(results[:10])  # Force evaluation
        end_time = time.time()
        
        # Search should complete within reasonable time
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
    
    def test_large_result_set_pagination(self):
        """Test pagination with large result sets."""
        results, snippets = AdvancedSearchEngine.search_posts('test')
        
        # Should handle large result sets efficiently
        self.assertIsNotNone(results)
        self.assertTrue(len(snippets) <= 50)  # Should limit results


class SearchIntegrationTestCase(TestCase):
    """
    Integration tests for complete search workflows.
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
            title='Python Web Development Guide',
            content='Complete guide to Python web development with Django framework',
            excerpt='Learn Python web development',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
    
    def test_complete_search_workflow(self):
        """Test complete search workflow from query to click tracking."""
        # 1. Perform search
        response = self.client.get(reverse('blog:search'), {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        
        # 2. Check that search was tracked
        search_queries = SearchQuery.objects.filter(query='python')
        self.assertTrue(search_queries.exists())
        
        search_query = search_queries.first()
        
        # 3. Simulate clicking on a result
        response = self.client.post(
            reverse('blog:track_search_click_api'),
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
    
    def test_search_facets_integration(self):
        """Test search facets integration with actual data."""
        # Perform search that should return facets
        response = self.client.get(reverse('blog:search'), {'q': 'python'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('facets', response.context)
        
        facets = response.context['facets']
        
        # Should contain category facets
        if facets['categories']:
            category_names = [cat['name'] for cat in facets['categories']]
            self.assertIn('Technology', category_names)
    
    def test_search_suggestions_integration(self):
        """Test search suggestions integration."""
        # Create search history
        SearchQuery.objects.create(
            query='python tutorial',
            results_count=1,
            ip_address='127.0.0.1'
        )
        
        # Test suggestions API
        response = self.client.get(
            reverse('blog:search_suggestions_api'),
            {'q': 'python'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should include historical suggestions
        self.assertTrue(len(data['suggestions']) > 0)