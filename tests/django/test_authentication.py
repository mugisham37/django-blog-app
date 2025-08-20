"""
Authentication system tests.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

@pytest.mark.auth
class TestAuthentication:
    """Test authentication endpoints and functionality."""
    
    def test_user_registration(self, api_client):
        """Test user registration endpoint."""
        url = reverse('auth:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='testuser').exists()
    
    def test_user_login(self, api_client, user):
        """Test user login endpoint."""
        url = reverse('auth:login')
        data = {
            'username': user.username,
            'password': 'testpassword'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
    
    def test_token_refresh(self, api_client, user):
        """Test JWT token refresh."""
        # First login to get tokens
        login_url = reverse('auth:login')
        login_data = {'username': user.username, 'password': 'testpassword'}
        login_response = api_client.post(login_url, login_data)
        
        refresh_token = login_response.data['refresh_token']
        
        # Test token refresh
        refresh_url = reverse('auth:token_refresh')
        refresh_data = {'refresh_token': refresh_token}
        response = api_client.post(refresh_url, refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
    
    def test_password_reset(self, api_client, user):
        """Test password reset functionality."""
        url = reverse('auth:password_reset')
        data = {'email': user.email}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_protected_endpoint_without_auth(self, api_client):
        """Test accessing protected endpoint without authentication."""
        url = reverse('auth:profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_auth(self, authenticated_client):
        """Test accessing protected endpoint with authentication."""
        url = reverse('auth:profile')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.auth
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_rate_limiting(self, api_client):
        """Test rate limiting on login attempts."""
        url = reverse('auth:login')
        data = {'username': 'nonexistent', 'password': 'wrong'}
        
        # Make multiple failed attempts
        for _ in range(10):
            response = api_client.post(url, data)
        
        # Should be rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_password_strength_validation(self, api_client):
        """Test password strength requirements."""
        url = reverse('auth:register')
        weak_passwords = ['123', 'password', 'abc123']
        
        for weak_password in weak_passwords:
            data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': weak_password,
                'password_confirm': weak_password
            }
            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_account_lockout(self, api_client, user):
        """Test account lockout after failed attempts."""
        url = reverse('auth:login')
        data = {'username': user.username, 'password': 'wrongpassword'}
        
        # Make multiple failed attempts
        for _ in range(5):
            api_client.post(url, data)
        
        # Account should be locked
        correct_data = {'username': user.username, 'password': 'testpassword'}
        response = api_client.post(url, correct_data)
        assert response.status_code == status.HTTP_423_LOCKED