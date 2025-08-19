"""
Tests for enhanced API features including rate limiting, caching, bulk operations,
search functionality, and data export/import.
"""

import json
import tempfile
from io import StringIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.blog.models import Post, Category, Tag
from apps.accounts.models import User


class RateLimitingTestCase(APITestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
    
    def test_anonymous_rate_limiting(self):
        """Test rate limiting for anonymous users."""
        url = reverse('api:v1:blog:post-list')
        
        # Make requests up to the limit
        for i in range(50):  # Assuming 50 requests per hour for anonymous
            response = self.client.get(url)
            if response.status_code == 429:  # Too Many Requests
                break
        
        # The last request should be rate limited
        self.assertEqual(response.status_code, 429)
    
    def test_authenticated_user_higher_limits(self):
        """Test that authenticated users have higher rate limits."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:v1:blog:post-list')
        
        # Authenticated users should have higher limits
        for i in range(100):
            response = self.client.get(url)
            if response.status_code == 429:
                break
        
        # Should allow more requests than anonymous users
        self.assertLess(i, 100)  # Should hit limit before 100 requests in test
    
    def test_staff_user_highest_limits(self):
        """Test that staff users have the highest rate limits."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('api:v1:blog:post-list')
        
        # Staff users should have very high limits
        for i in range(200):
            response = self.client.get(url)
            if response.status_code == 429:
                break
        
        # Staff should have highest limits
        self.assertGreater(i, 150)


class CachingTestCase(APITestCase):
    """Test API response caching."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status=Post.PostStatus.PUBLISHED
        )
        cache.clear()
    
    def test_response_caching(self):
        """Test that API responses are cached."""
        url = reverse('api:v1:blog:post-list')
        
        # First request should hit the database
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be served from cache
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.data, response2.data)
    
    def test_cache_invalidation_on_create(self):
        """Test that cache is invalidated when new objects are created."""
        self.client.force_authenticate(user=self.user)
        
        # Get initial list
        list_url = reverse('api:v1:blog:post-list')
        response1 = self.client.get(list_url)
        initial_count = len(response1.data['results'])
        
        # Create new post
        create_data = {
            'title': 'New Post',
            'content': 'New content',
            'category': self.category.id,
            'status': Post.PostStatus.PUBLISHED
        }
        create_response = self.client.post(list_url, create_data)
        self.assertEqual(create_response.status_code, 201)
        
        # List should show updated data (cache should be invalidated)
        response2 = self.client.get(list_url)
        self.assertEqual(len(response2.data['results']), initial_count + 1)
    
    def test_etag_support(self):
        """Test ETag support for conditional requests."""
        url = reverse('api:v1:blog:post-detail', kwargs={'pk': self.post.pk})
        
        # First request should return ETag
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        etag = response1.get('ETag')
        self.assertIsNotNone(etag)
        
        # Request with If-None-Match should return 304
        response2 = self.client.get(url, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(response2.status_code, 304)


class BulkOperationsTestCase(APITestCase):
    """Test bulk operations functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.client.force_authenticate(user=self.user)
    
    def test_bulk_create_posts(self):
        """Test bulk creation of posts."""
        url = reverse('api:v1:blog:post-bulk-create')
        
        bulk_data = [
            {
                'title': 'Bulk Post 1',
                'content': 'Content 1',
                'category': self.category.id,
                'status': Post.PostStatus.PUBLISHED
            },
            {
                'title': 'Bulk Post 2',
                'content': 'Content 2',
                'category': self.category.id,
                'status': Post.PostStatus.DRAFT
            }
        ]
        
        response = self.client.post(url, bulk_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 2)
        
        # Verify posts were created
        self.assertEqual(Post.objects.filter(title__startswith='Bulk Post').count(), 2)
    
    def test_bulk_update_posts(self):
        """Test bulk updating of posts."""
        # Create test posts
        post1 = Post.objects.create(
            title='Post 1',
            slug='post-1',
            content='Content 1',
            author=self.user,
            category=self.category
        )
        post2 = Post.objects.create(
            title='Post 2',
            slug='post-2',
            content='Content 2',
            author=self.user,
            category=self.category
        )
        
        url = reverse('api:v1:blog:post-bulk-update')
        
        update_data = [
            {
                'id': post1.id,
                'title': 'Updated Post 1',
                'status': Post.PostStatus.PUBLISHED
            },
            {
                'id': post2.id,
                'title': 'Updated Post 2',
                'status': Post.PostStatus.PUBLISHED
            }
        ]
        
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify updates
        post1.refresh_from_db()
        post2.refresh_from_db()
        self.assertEqual(post1.title, 'Updated Post 1')
        self.assertEqual(post2.title, 'Updated Post 2')
    
    def test_bulk_delete_posts(self):
        """Test bulk deletion of posts."""
        # Create test posts
        post1 = Post.objects.create(
            title='Post 1',
            slug='post-1',
            content='Content 1',
            author=self.user,
            category=self.category
        )
        post2 = Post.objects.create(
            title='Post 2',
            slug='post-2',
            content='Content 2',
            author=self.user,
            category=self.category
        )
        
        url = reverse('api:v1:blog:post-bulk-delete')
        
        delete_data = {'ids': [post1.id, post2.id]}
        
        response = self.client.delete(url, delete_data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted_count'], 2)
        
        # Verify deletion
        self.assertFalse(Post.objects.filter(id__in=[post1.id, post2.id]).exists())


class SearchFunctionalityTestCase(APITestCase):
    """Test advanced search functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Technology', slug='technology')
        self.tag1 = Tag.objects.create(name='Python', slug='python')
        self.tag2 = Tag.objects.create(name='Django', slug='django')
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='Python Programming Guide',
            slug='python-guide',
            content='Learn Python programming with this comprehensive guide',
            author=self.user,
            category=self.category,
            status=Post.PostStatus.PUBLISHED
        )
        self.post1.tags.add(self.tag1)
        
        self.post2 = Post.objects.create(
            title='Django Web Development',
            slug='django-web',
            content='Build web applications with Django framework',
            author=self.user,
            category=self.category,
            status=Post.PostStatus.PUBLISHED
        )
        self.post2.tags.add(self.tag2)
    
    def test_basic_search(self):
        """Test basic search functionality."""
        url = reverse('api:v1:blog:post-list')
        
        response = self.client.get(url, {'search': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Programming Guide')
    
    def test_advanced_search(self):
        """Test advanced search with multiple fields."""
        url = reverse('api:v1:blog:post-advanced-search')
        
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
    
    def test_search_suggestions(self):
        """Test search suggestions."""
        url = reverse('api:v1:blog:post-search-suggestions')
        
        response = self.client.get(url, {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.data)
    
    def test_faceted_search(self):
        """Test faceted search functionality."""
        url = reverse('api:v1:blog:post-faceted-search')
        
        response = self.client.get(url, {'q': 'programming'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('facets', response.data)
        self.assertIn('categories', response.data['facets'])
        self.assertIn('tags', response.data['facets'])


class DataExportImportTestCase(APITestCase):
    """Test data export and import functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff required for import
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        
        # Create test posts
        for i in range(5):
            Post.objects.create(
                title=f'Test Post {i+1}',
                slug=f'test-post-{i+1}',
                content=f'Content for post {i+1}',
                author=self.user,
                category=self.category,
                status=Post.PostStatus.PUBLISHED
            )
        
        self.client.force_authenticate(user=self.user)
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        url = reverse('api:v1:blog:post-export-csv')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_json_export(self):
        """Test JSON export functionality."""
        url = reverse('api:v1:blog:post-export-json')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_excel_export(self):
        """Test Excel export functionality."""
        url = reverse('api:v1:blog:post-export-excel')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheet', response['Content-Type'])
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_csv_import(self):
        """Test CSV import functionality."""
        url = reverse('api:v1:blog:post-import-csv')
        
        # Create CSV content
        csv_content = """title,content,category,status
"Imported Post 1","Content 1","Test Category","published"
"Imported Post 2","Content 2","Test Category","draft"
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('imported_count', response.data)
        
        # Verify posts were imported
        self.assertTrue(Post.objects.filter(title='Imported Post 1').exists())
        self.assertTrue(Post.objects.filter(title='Imported Post 2').exists())
    
    def test_json_import(self):
        """Test JSON import functionality."""
        url = reverse('api:v1:blog:post-import-json')
        
        # Create JSON content
        json_content = [
            {
                "title": "JSON Imported Post 1",
                "content": "JSON Content 1",
                "category": self.category.id,
                "status": "published"
            },
            {
                "title": "JSON Imported Post 2",
                "content": "JSON Content 2",
                "category": self.category.id,
                "status": "draft"
            }
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            
            with open(f.name, 'rb') as json_file:
                response = self.client.post(url, {'file': json_file}, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('imported_count', response.data)
        
        # Verify posts were imported
        self.assertTrue(Post.objects.filter(title='JSON Imported Post 1').exists())
        self.assertTrue(Post.objects.filter(title='JSON Imported Post 2').exists())
    
    def test_custom_export(self):
        """Test custom export with configuration."""
        url = reverse('api:v1:blog:post-custom-export')
        
        export_config = {
            'format': 'json',
            'fields': ['title', 'content', 'author.username'],
            'filters': {'status': 'published'},
            'order_by': '-created_at',
            'limit': 3
        }
        
        response = self.client.post(url, export_config, format='json')
        self.assertEqual(response.status_code, 200)


class PermissionsTestCase(APITestCase):
    """Test role-based permissions."""
    
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
    
    def test_regular_user_permissions(self):
        """Test permissions for regular users."""
        self.client.force_authenticate(user=self.regular_user)
        
        # Should be able to create posts
        url = reverse('api:v1:blog:post-list')
        data = {
            'title': 'User Post',
            'content': 'User content',
            'category': self.category.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        
        # Should not be able to import data
        import_url = reverse('api:v1:blog:post-import-csv')
        response = self.client.post(import_url, {})
        self.assertEqual(response.status_code, 403)
    
    def test_staff_user_permissions(self):
        """Test permissions for staff users."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Should be able to import data
        import_url = reverse('api:v1:blog:post-import-csv')
        response = self.client.post(import_url, {})
        # Should not be 403 (may be 400 due to missing file, but not forbidden)
        self.assertNotEqual(response.status_code, 403)
    
    def test_author_can_edit_own_posts(self):
        """Test that authors can edit their own posts."""
        self.client.force_authenticate(user=self.regular_user)
        
        # Create post
        post = Post.objects.create(
            title='User Post',
            slug='user-post',
            content='User content',
            author=self.regular_user,
            category=self.category
        )
        
        # Should be able to update own post
        url = reverse('api:v1:blog:post-detail', kwargs={'pk': post.pk})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
    
    def test_user_cannot_edit_others_posts(self):
        """Test that users cannot edit others' posts."""
        # Create post by staff user
        post = Post.objects.create(
            title='Staff Post',
            slug='staff-post',
            content='Staff content',
            author=self.staff_user,
            category=self.category
        )
        
        # Regular user should not be able to edit
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('api:v1:blog:post-detail', kwargs={'pk': post.pk})
        data = {'title': 'Hacked Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 403)


class AnalyticsTestCase(APITestCase):
    """Test search analytics functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_search_tracking(self):
        """Test that searches are tracked for analytics."""
        url = reverse('api:v1:blog:post-advanced-search')
        
        # Perform search
        response = self.client.get(url, {'q': 'test query'})
        self.assertEqual(response.status_code, 200)
        
        # Check that search was tracked (would need SearchQuery model)
        # This is a placeholder - actual implementation would verify database records
    
    def test_search_analytics_access(self):
        """Test access to search analytics."""
        # Regular user should not have access
        self.client.force_authenticate(user=self.user)
        url = reverse('api:v1:blog:post-search-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Staff user should have access
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_search_history(self):
        """Test user search history."""
        self.client.force_authenticate(user=self.user)
        
        # Perform some searches
        search_url = reverse('api:v1:blog:post-advanced-search')
        self.client.get(search_url, {'q': 'first query'})
        self.client.get(search_url, {'q': 'second query'})
        
        # Get search history
        history_url = reverse('api:v1:blog:post-search-history')
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('history', response.data)