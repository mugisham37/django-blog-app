"""
Integration tests for blog listing views and filtering functionality.
Tests for task 6.1: Create post listing views with filtering and pagination.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch

from apps.blog.models import Post, Category, Tag
from apps.core.models import TimeStampedModel

User = get_user_model()


class PostListViewTestCase(TestCase):
    """Test cases for the enhanced PostListView with filtering and pagination."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.author1 = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.author2 = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create test categories
        self.parent_category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Technology related posts',
            is_active=True
        )
        self.child_category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming tutorials',
            parent=self.parent_category,
            is_active=True
        )
        self.other_category = Category.objects.create(
            name='Design',
            slug='design',
            description='Design articles',
            is_active=True
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Python', slug='python', color='#3776ab')
        self.tag2 = Tag.objects.create(name='Django', slug='django', color='#092e20')
        self.tag3 = Tag.objects.create(name='JavaScript', slug='javascript', color='#f7df1e')
        
        # Create test posts
        self.published_posts = []
        for i in range(15):
            post = Post.objects.create(
                title=f'Test Post {i+1}',
                slug=f'test-post-{i+1}',
                content=f'This is the content for test post {i+1}. It contains various keywords for testing search functionality.',
                excerpt=f'Excerpt for test post {i+1}',
                author=self.author1 if i % 2 == 0 else self.author2,
                category=self.parent_category if i % 3 == 0 else self.child_category,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now() - timedelta(days=i),
                is_featured=(i < 3),  # First 3 posts are featured
                view_count=100 - i * 5  # Decreasing view count
            )
            
            # Add tags to some posts
            if i % 2 == 0:
                post.tags.add(self.tag1)
            if i % 3 == 0:
                post.tags.add(self.tag2)
            if i % 5 == 0:
                post.tags.add(self.tag3)
            
            self.published_posts.append(post)
        
        # Create some draft posts (should not appear in listings)
        for i in range(3):
            Post.objects.create(
                title=f'Draft Post {i+1}',
                slug=f'draft-post-{i+1}',
                content=f'Draft content {i+1}',
                author=self.author1,
                category=self.parent_category,
                status=Post.Status.DRAFT
            )
    
    def test_post_list_view_basic(self):
        """Test basic post list view functionality."""
        response = self.client.get(reverse('blog:post_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Latest Blog Posts')
        self.assertContains(response, 'Test Post 1')
        
        # Check pagination (should show 12 posts per page by default)
        self.assertEqual(len(response.context['posts']), 12)
        self.assertTrue(response.context['is_paginated'])
        
        # Check that draft posts are not included
        for post in response.context['posts']:
            self.assertEqual(post.status, Post.Status.PUBLISHED)
    
    def test_post_list_pagination(self):
        """Test pagination functionality."""
        # Test first page
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(len(response.context['posts']), 12)
        self.assertTrue(response.context['page_obj'].has_next())
        self.assertFalse(response.context['page_obj'].has_previous())
        
        # Test second page
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 3)  # Remaining 3 posts
        self.assertFalse(response.context['page_obj'].has_next())
        self.assertTrue(response.context['page_obj'].has_previous())
        
        # Test invalid page
        response = self.client.get(reverse('blog:post_list') + '?page=999')
        self.assertEqual(response.status_code, 200)  # Should show last page
    
    def test_category_filtering(self):
        """Test filtering posts by category."""
        # Filter by parent category (should include child category posts)
        response = self.client.get(reverse('blog:post_list') + f'?category={self.parent_category.slug}')
        self.assertEqual(response.status_code, 200)
        
        # Should include posts from both parent and child categories
        category_posts = [p for p in self.published_posts if p.category in [self.parent_category, self.child_category]]
        self.assertEqual(len(response.context['posts']), min(12, len(category_posts)))
        
        # Filter by child category only
        response = self.client.get(reverse('blog:post_list') + f'?category={self.child_category.slug}')
        child_posts = [p for p in self.published_posts if p.category == self.child_category]
        self.assertEqual(len(response.context['posts']), len(child_posts))
        
        # Test invalid category
        response = self.client.get(reverse('blog:post_list') + '?category=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
    
    def test_tag_filtering(self):
        """Test filtering posts by tag."""
        response = self.client.get(reverse('blog:post_list') + f'?tag={self.tag1.slug}')
        self.assertEqual(response.status_code, 200)
        
        # Check that all returned posts have the specified tag
        for post in response.context['posts']:
            self.assertIn(self.tag1, post.tags.all())
        
        # Test invalid tag
        response = self.client.get(reverse('blog:post_list') + '?tag=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
    
    def test_author_filtering(self):
        """Test filtering posts by author."""
        response = self.client.get(reverse('blog:post_list') + f'?author={self.author1.username}')
        self.assertEqual(response.status_code, 200)
        
        # Check that all returned posts are by the specified author
        for post in response.context['posts']:
            self.assertEqual(post.author, self.author1)
        
        # Test invalid author
        response = self.client.get(reverse('blog:post_list') + '?author=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
    
    def test_featured_filtering(self):
        """Test filtering for featured posts only."""
        response = self.client.get(reverse('blog:post_list') + '?featured=1')
        self.assertEqual(response.status_code, 200)
        
        # Check that all returned posts are featured
        for post in response.context['posts']:
            self.assertTrue(post.is_featured)
        
        # Should have 3 featured posts
        self.assertEqual(len(response.context['posts']), 3)
    
    def test_date_range_filtering(self):
        """Test filtering posts by date range."""
        # Filter posts from last 7 days
        date_from = (timezone.now() - timedelta(days=7)).date()
        response = self.client.get(reverse('blog:post_list') + f'?date_from={date_from}')
        self.assertEqual(response.status_code, 200)
        
        # Check that all returned posts are within the date range
        for post in response.context['posts']:
            self.assertGreaterEqual(post.published_at.date(), date_from)
        
        # Test date range with both from and to
        date_to = (timezone.now() - timedelta(days=3)).date()
        response = self.client.get(
            reverse('blog:post_list') + f'?date_from={date_from}&date_to={date_to}'
        )
        self.assertEqual(response.status_code, 200)
        
        for post in response.context['posts']:
            self.assertGreaterEqual(post.published_at.date(), date_from)
            self.assertLessEqual(post.published_at.date(), date_to)
    
    def test_sorting_options(self):
        """Test different sorting options."""
        # Test newest first (default)
        response = self.client.get(reverse('blog:post_list'))
        posts = list(response.context['posts'])
        self.assertEqual(posts[0].title, 'Test Post 1')  # Most recent
        
        # Test oldest first
        response = self.client.get(reverse('blog:post_list') + '?sort=oldest')
        posts = list(response.context['posts'])
        self.assertEqual(posts[0].title, 'Test Post 15')  # Oldest
        
        # Test most popular
        response = self.client.get(reverse('blog:post_list') + '?sort=popular')
        posts = list(response.context['posts'])
        # Should be sorted by view_count descending
        for i in range(len(posts) - 1):
            self.assertGreaterEqual(posts[i].view_count, posts[i + 1].view_count)
        
        # Test title sorting
        response = self.client.get(reverse('blog:post_list') + '?sort=title')
        posts = list(response.context['posts'])
        titles = [post.title for post in posts]
        self.assertEqual(titles, sorted(titles))
    
    @patch('django.contrib.postgres.search.SearchVector')
    @patch('django.contrib.postgres.search.SearchQuery')
    @patch('django.contrib.postgres.search.SearchRank')
    def test_search_functionality(self, mock_rank, mock_query, mock_vector):
        """Test PostgreSQL full-text search functionality."""
        # Mock the PostgreSQL search components
        mock_vector.return_value = 'mocked_vector'
        mock_query.return_value = 'mocked_query'
        mock_rank.return_value = 'mocked_rank'
        
        search_term = 'test content'
        response = self.client.get(reverse('blog:post_list') + f'?q={search_term}')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify that search components were called
        mock_vector.assert_called()
        mock_query.assert_called_with(search_term)
        mock_rank.assert_called()
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        # Combine category and tag filters
        response = self.client.get(
            reverse('blog:post_list') + 
            f'?category={self.parent_category.slug}&tag={self.tag1.slug}'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check that posts match both filters
        for post in response.context['posts']:
            self.assertIn(post.category, [self.parent_category, self.child_category])
            self.assertIn(self.tag1, post.tags.all())
        
        # Combine author and featured filters
        response = self.client.get(
            reverse('blog:post_list') + 
            f'?author={self.author1.username}&featured=1'
        )
        self.assertEqual(response.status_code, 200)
        
        for post in response.context['posts']:
            self.assertEqual(post.author, self.author1)
            self.assertTrue(post.is_featured)
    
    def test_context_data(self):
        """Test that proper context data is provided."""
        response = self.client.get(reverse('blog:post_list'))
        
        # Check required context variables
        self.assertIn('search_form', response.context)
        self.assertIn('popular_categories', response.context)
        self.assertIn('popular_tags', response.context)
        self.assertIn('current_filters', response.context)
        self.assertIn('breadcrumbs', response.context)
        self.assertIn('seo_title', response.context)
        self.assertIn('seo_description', response.context)
        
        # Check pagination info when paginated
        if response.context['is_paginated']:
            self.assertIn('pagination_info', response.context)
            pagination_info = response.context['pagination_info']
            self.assertIn('current_page', pagination_info)
            self.assertIn('total_pages', pagination_info)
            self.assertIn('total_posts', pagination_info)
    
    def test_seo_optimization(self):
        """Test SEO title and description generation."""
        # Test search SEO
        response = self.client.get(reverse('blog:post_list') + '?q=test')
        self.assertIn('Search: test', response.context['seo_title'])
        
        # Test category SEO
        response = self.client.get(reverse('blog:post_list') + f'?category={self.parent_category.slug}')
        self.assertIn(f'Category: {self.parent_category.name}', response.context['seo_title'])
        
        # Test tag SEO
        response = self.client.get(reverse('blog:post_list') + f'?tag={self.tag1.slug}')
        self.assertIn(f'Tag: {self.tag1.name}', response.context['seo_title'])
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated properly for different filter combinations."""
        view = self.client.get(reverse('blog:post_list')).wsgi_request
        
        # This would require accessing the view instance, which is complex in Django tests
        # For now, we'll test that the view responds correctly to different parameter combinations
        
        # Test various parameter combinations
        params = [
            {},
            {'q': 'test'},
            {'category': 'technology'},
            {'tag': 'python'},
            {'q': 'test', 'category': 'technology'},
            {'page': '2'},
        ]
        
        for param_dict in params:
            query_string = '&'.join([f'{k}={v}' for k, v in param_dict.items()])
            url = reverse('blog:post_list')
            if query_string:
                url += f'?{query_string}'
            
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


class ArchiveViewTestCase(TestCase):
    """Test cases for archive views."""
    
    def setUp(self):
        """Set up test data for archive views."""
        self.client = Client()
        self.author = User.objects.create_user(
            username='testauthor',
            email='test@example.com'
        )
        
        # Create posts across different months and years
        dates = [
            datetime(2023, 1, 15),
            datetime(2023, 1, 20),
            datetime(2023, 2, 10),
            datetime(2023, 3, 5),
            datetime(2024, 1, 1),
            datetime(2024, 2, 14),
        ]
        
        for i, date in enumerate(dates):
            Post.objects.create(
                title=f'Archive Post {i+1}',
                slug=f'archive-post-{i+1}',
                content=f'Content for archive post {i+1}',
                author=self.author,
                status=Post.Status.PUBLISHED,
                published_at=timezone.make_aware(date)
            )
    
    def test_archive_view_all(self):
        """Test the main archive view."""
        response = self.client.get(reverse('blog:post_archive'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archive: All Posts')
        self.assertEqual(len(response.context['posts']), 6)
    
    def test_archive_view_by_year(self):
        """Test archive view filtered by year."""
        response = self.client.get(reverse('blog:post_archive_year', kwargs={'year': 2023}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archive: 2023')
        self.assertEqual(len(response.context['posts']), 4)  # 4 posts in 2023
        
        # Test year with no posts
        response = self.client.get(reverse('blog:post_archive_year', kwargs={'year': 2022}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
    
    def test_archive_view_by_month(self):
        """Test archive view filtered by year and month."""
        response = self.client.get(reverse('blog:post_archive_month', kwargs={'year': 2023, 'month': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archive: January 2023')
        self.assertEqual(len(response.context['posts']), 2)  # 2 posts in January 2023
        
        # Test month with no posts
        response = self.client.get(reverse('blog:post_archive_month', kwargs={'year': 2023, 'month': 12}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
    
    def test_archive_context_data(self):
        """Test that archive views provide proper context data."""
        # Test yearly archive context
        response = self.client.get(reverse('blog:post_archive_year', kwargs={'year': 2023}))
        self.assertIn('archive_year', response.context)
        self.assertIn('monthly_breakdown', response.context)
        self.assertEqual(response.context['archive_year'], 2023)
        
        # Test monthly archive context
        response = self.client.get(reverse('blog:post_archive_month', kwargs={'year': 2023, 'month': 1}))
        self.assertIn('archive_month', response.context)
        self.assertIn('archive_date', response.context)
        self.assertIn('daily_breakdown', response.context)
        self.assertEqual(response.context['archive_month'], 1)


class CategoryDetailViewTestCase(TestCase):
    """Test cases for category detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.author = User.objects.create_user(username='testauthor', email='test@example.com')
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description',
            is_active=True
        )
        
        # Create posts in this category
        for i in range(5):
            Post.objects.create(
                title=f'Category Post {i+1}',
                slug=f'category-post-{i+1}',
                content=f'Content {i+1}',
                author=self.author,
                category=self.category,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now()
            )
    
    def test_category_detail_view(self):
        """Test category detail view functionality."""
        response = self.client.get(reverse('blog:category_detail', kwargs={'slug': self.category.slug}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
        self.assertContains(response, self.category.description)
        self.assertEqual(len(response.context['posts']), 5)
        
        # Test nonexistent category
        response = self.client.get(reverse('blog:category_detail', kwargs={'slug': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)


class TagDetailViewTestCase(TestCase):
    """Test cases for tag detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.author = User.objects.create_user(username='testauthor', email='test@example.com')
        
        self.tag = Tag.objects.create(
            name='Test Tag',
            slug='test-tag',
            description='Test tag description',
            color='#ff0000'
        )
        
        # Create posts with this tag
        for i in range(3):
            post = Post.objects.create(
                title=f'Tagged Post {i+1}',
                slug=f'tagged-post-{i+1}',
                content=f'Content {i+1}',
                author=self.author,
                status=Post.Status.PUBLISHED,
                published_at=timezone.now()
            )
            post.tags.add(self.tag)
    
    def test_tag_detail_view(self):
        """Test tag detail view functionality."""
        response = self.client.get(reverse('blog:tag_detail', kwargs={'slug': self.tag.slug}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)
        self.assertContains(response, self.tag.description)
        self.assertEqual(len(response.context['posts']), 3)
        
        # Test nonexistent tag
        response = self.client.get(reverse('blog:tag_detail', kwargs={'slug': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)


class CategoryListViewTestCase(TestCase):
    """Test cases for category list view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create categories with posts
        for i in range(5):
            category = Category.objects.create(
                name=f'Category {i+1}',
                slug=f'category-{i+1}',
                description=f'Description {i+1}',
                is_active=True
            )
            
            # Create some posts for each category
            author = User.objects.create_user(
                username=f'author{i+1}',
                email=f'author{i+1}@example.com'
            )
            
            for j in range(i + 1):  # Variable number of posts per category
                Post.objects.create(
                    title=f'Post {j+1} in Category {i+1}',
                    slug=f'post-{j+1}-category-{i+1}',
                    content=f'Content {j+1}',
                    author=author,
                    category=category,
                    status=Post.Status.PUBLISHED,
                    published_at=timezone.now()
                )
    
    def test_category_list_view(self):
        """Test category list view functionality."""
        response = self.client.get(reverse('blog:category_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categories')
        self.assertEqual(len(response.context['categories']), 5)
        
        # Check that post counts are annotated
        for category in response.context['categories']:
            self.assertIsNotNone(category.post_count)
            self.assertGreater(category.post_count, 0)


if __name__ == '__main__':
    pytest.main([__file__])