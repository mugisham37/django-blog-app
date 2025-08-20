"""
API endpoint tests for all Django apps.
"""
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.api
class TestBlogAPI:
    """Test blog-related API endpoints."""
    
    def test_post_list(self, api_client, post_factory):
        """Test blog post listing endpoint."""
        # Create test posts
        posts = post_factory.create_batch(5)
        
        url = reverse('blog:post-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_post_detail(self, api_client, post_factory):
        """Test blog post detail endpoint."""
        post = post_factory()
        
        url = reverse('blog:post-detail', kwargs={'slug': post.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == post.title
    
    def test_post_create_authenticated(self, authenticated_client):
        """Test creating blog post with authentication."""
        url = reverse('blog:post-list')
        data = {
            'title': 'Test Post',
            'content': 'Test content',
            'status': 'draft'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Post'
    
    def test_post_create_unauthenticated(self, api_client):
        """Test creating blog post without authentication."""
        url = reverse('blog:post-list')
        data = {
            'title': 'Test Post',
            'content': 'Test content'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_post_filtering(self, api_client, post_factory, category_factory):
        """Test blog post filtering by category."""
        category = category_factory()
        posts = post_factory.create_batch(3, category=category)
        other_posts = post_factory.create_batch(2)
        
        url = reverse('blog:post-list')
        response = api_client.get(url, {'category': category.slug})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_post_search(self, api_client, post_factory):
        """Test blog post search functionality."""
        post = post_factory(title='Unique Search Term')
        other_posts = post_factory.create_batch(3)
        
        url = reverse('blog:post-list')
        response = api_client.get(url, {'search': 'Unique Search'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Unique Search Term'

@pytest.mark.api
class TestCommentAPI:
    """Test comment-related API endpoints."""
    
    def test_comment_list(self, api_client, comment_factory):
        """Test comment listing for a post."""
        comments = comment_factory.create_batch(3)
        post = comments[0].post
        
        url = reverse('blog:comment-list', kwargs={'post_slug': post.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_comment_create(self, authenticated_client, post_factory):
        """Test creating a comment."""
        post = post_factory()
        
        url = reverse('blog:comment-list', kwargs={'post_slug': post.slug})
        data = {
            'content': 'Test comment content'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Test comment content'

@pytest.mark.api
class TestUserAPI:
    """Test user-related API endpoints."""
    
    def test_user_profile(self, authenticated_client, user):
        """Test user profile endpoint."""
        url = reverse('accounts:profile')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
    
    def test_user_profile_update(self, authenticated_client):
        """Test updating user profile."""
        url = reverse('accounts:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'

@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance benchmarks."""
    
    def test_post_list_performance(self, api_client, post_factory, benchmark):
        """Benchmark post list endpoint performance."""
        post_factory.create_batch(100)
        
        url = reverse('blog:post-list')
        
        def make_request():
            return api_client.get(url)
        
        result = benchmark(make_request)
        assert result.status_code == status.HTTP_200_OK
    
    def test_post_search_performance(self, api_client, post_factory, benchmark):
        """Benchmark post search performance."""
        post_factory.create_batch(1000)
        
        url = reverse('blog:post-list')
        
        def search_request():
            return api_client.get(url, {'search': 'test'})
        
        result = benchmark(search_request)
        assert result.status_code == status.HTTP_200_OK