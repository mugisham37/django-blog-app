"""
Tests for JWT and OAuth2 authentication strategies.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from auth_package.strategies import (
    JWTStrategy, JWTConfig, OAuth2Strategy, TokenPair,
    setup_google_oauth2, setup_github_oauth2, setup_facebook_oauth2,
    setup_microsoft_oauth2, setup_linkedin_oauth2
)


class TestJWTStrategy:
    """Test JWT authentication strategy."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = JWTConfig(
            secret_key="test-secret-key",
            access_token_lifetime=timedelta(minutes=15),
            refresh_token_lifetime=timedelta(days=7)
        )
        self.jwt_strategy = JWTStrategy(self.config)
    
    def test_generate_tokens(self):
        """Test token generation."""
        user_id = "user123"
        user_data = {"email": "test@example.com", "roles": ["user"]}
        
        tokens = self.jwt_strategy.generate_tokens(user_id, user_data)
        
        assert isinstance(tokens, TokenPair)
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.expires_in == int(self.config.access_token_lifetime.total_seconds())
        assert tokens.token_type == "Bearer"
    
    def test_validate_access_token(self):
        """Test access token validation."""
        user_id = "user123"
        user_data = {"email": "test@example.com"}
        
        tokens = self.jwt_strategy.generate_tokens(user_id, user_data)
        payload = self.jwt_strategy.validate_token(tokens.access_token, "access")
        
        assert payload["user_id"] == user_id
        assert payload["email"] == user_data["email"]
        assert payload["type"] == "access"
        assert payload["iss"] == self.config.issuer
        assert payload["aud"] == self.config.audience
    
    def test_validate_refresh_token(self):
        """Test refresh token validation."""
        user_id = "user123"
        
        tokens = self.jwt_strategy.generate_tokens(user_id)
        payload = self.jwt_strategy.validate_token(tokens.refresh_token, "refresh")
        
        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"
        assert "token_id" in payload
    
    def test_refresh_access_token(self):
        """Test access token refresh."""
        user_id = "user123"
        
        original_tokens = self.jwt_strategy.generate_tokens(user_id)
        new_tokens = self.jwt_strategy.refresh_access_token(original_tokens.refresh_token)
        
        assert isinstance(new_tokens, TokenPair)
        assert new_tokens.access_token != original_tokens.access_token
        assert new_tokens.refresh_token != original_tokens.refresh_token
    
    def test_invalid_token_validation(self):
        """Test validation of invalid tokens."""
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_strategy.validate_token("invalid-token")
    
    def test_expired_token_validation(self):
        """Test validation of expired tokens."""
        # Create strategy with very short token lifetime
        short_config = JWTConfig(
            secret_key="test-secret",
            access_token_lifetime=timedelta(seconds=-1)  # Already expired
        )
        short_strategy = JWTStrategy(short_config)
        
        tokens = short_strategy.generate_tokens("user123")
        
        with pytest.raises(jwt.InvalidTokenError):
            short_strategy.validate_token(tokens.access_token)
    
    def test_wrong_token_type_validation(self):
        """Test validation with wrong token type."""
        tokens = self.jwt_strategy.generate_tokens("user123")
        
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_strategy.validate_token(tokens.access_token, "refresh")
    
    def test_revoke_refresh_token(self):
        """Test refresh token revocation."""
        tokens = self.jwt_strategy.generate_tokens("user123")
        
        # Token should be valid initially
        payload = self.jwt_strategy.validate_token(tokens.refresh_token, "refresh")
        assert payload is not None
        
        # Revoke token
        revoked = self.jwt_strategy.revoke_refresh_token(tokens.refresh_token)
        assert revoked is True
        
        # Token should be invalid after revocation
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_strategy.validate_token(tokens.refresh_token, "refresh")
    
    def test_revoke_all_user_tokens(self):
        """Test revoking all tokens for a user."""
        user_id = "user123"
        
        # Generate multiple tokens
        tokens1 = self.jwt_strategy.generate_tokens(user_id)
        tokens2 = self.jwt_strategy.generate_tokens(user_id)
        
        # Revoke all tokens for user
        revoked_count = self.jwt_strategy.revoke_all_user_tokens(user_id)
        assert revoked_count == 2
        
        # All tokens should be invalid
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_strategy.validate_token(tokens1.refresh_token, "refresh")
        
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_strategy.validate_token(tokens2.refresh_token, "refresh")


class TestOAuth2Strategy:
    """Test OAuth2 authentication strategy."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.oauth2 = OAuth2Strategy()
        self.provider_config = OAuth2Strategy.ProviderConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            authorization_url="https://provider.com/oauth/authorize",
            token_url="https://provider.com/oauth/token",
            user_info_url="https://provider.com/oauth/userinfo",
            redirect_uri="https://app.com/callback"
        )
        self.oauth2.register_provider("test_provider", self.provider_config)
    
    def test_register_provider(self):
        """Test provider registration."""
        assert "test_provider" in self.oauth2.providers
        assert self.oauth2.providers["test_provider"] == self.provider_config
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        state = "test_state"
        auth_url = self.oauth2.get_authorization_url("test_provider", state)
        
        assert auth_url.startswith(self.provider_config.authorization_url)
        assert f"client_id={self.provider_config.client_id}" in auth_url
        assert f"redirect_uri={self.provider_config.redirect_uri}" in auth_url
        assert f"state={state}" in auth_url
        assert "response_type=code" in auth_url
    
    def test_get_authorization_url_unknown_provider(self):
        """Test authorization URL with unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            self.oauth2.get_authorization_url("unknown_provider")
    
    @patch('requests.post')
    def test_exchange_code_for_token(self, mock_post):
        """Test code exchange for token."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        token_data = self.oauth2.exchange_code_for_token("test_provider", "auth_code")
        
        assert token_data["access_token"] == "test_access_token"
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_get_user_info(self, mock_get):
        """Test user info retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "123",
            "email": "user@example.com",
            "name": "Test User"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        user_info = self.oauth2.get_user_info("test_provider", "access_token")
        
        assert user_info["email"] == "user@example.com"
        mock_get.assert_called_once_with(
            self.provider_config.user_info_url,
            headers={"Authorization": "Bearer access_token"}
        )
    
    def test_exchange_code_unknown_provider(self):
        """Test code exchange with unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            self.oauth2.exchange_code_for_token("unknown_provider", "code")
    
    def test_get_user_info_unknown_provider(self):
        """Test user info with unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            self.oauth2.get_user_info("unknown_provider", "token")


class TestJWTConfig:
    """Test JWT configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = JWTConfig(secret_key="test")
        
        assert config.secret_key == "test"
        assert config.algorithm == "HS256"
        assert config.access_token_lifetime == timedelta(minutes=15)
        assert config.refresh_token_lifetime == timedelta(days=7)
        assert config.issuer == "auth-package"
        assert config.audience == "api"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = JWTConfig(
            secret_key="custom-secret",
            algorithm="RS256",
            access_token_lifetime=timedelta(hours=1),
            refresh_token_lifetime=timedelta(days=30),
            issuer="custom-issuer",
            audience="custom-audience"
        )
        
        assert config.secret_key == "custom-secret"
        assert config.algorithm == "RS256"
        assert config.access_token_lifetime == timedelta(hours=1)
        assert config.refresh_token_lifetime == timedelta(days=30)
        assert config.issuer == "custom-issuer"
        assert config.audience == "custom-audience"


class TestTokenPair:
    """Test TokenPair data structure."""
    
    def test_token_pair_creation(self):
        """Test TokenPair creation."""
        token_pair = TokenPair(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=3600
        )
        
        assert token_pair.access_token == "access_token"
        assert token_pair.refresh_token == "refresh_token"
        assert token_pair.expires_in == 3600
        assert token_pair.token_type == "Bearer"
    
    def test_token_pair_custom_type(self):
        """Test TokenPair with custom token type."""
        token_pair = TokenPair(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=3600,
            token_type="Custom"
        )
        
        assert token_pair.token_type == "Custom"


class TestOAuth2ProviderSetup:
    """Test OAuth2 provider setup functions."""
    
    def test_setup_google_oauth2(self):
        """Test Google OAuth2 provider setup."""
        config = setup_google_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "https://app.com/callback"
        assert "accounts.google.com" in config.authorization_url
        assert "oauth2.googleapis.com" in config.token_url
        assert "googleapis.com" in config.user_info_url
        assert "openid profile email" in config.scope
    
    def test_setup_github_oauth2(self):
        """Test GitHub OAuth2 provider setup."""
        config = setup_github_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "https://app.com/callback"
        assert "github.com" in config.authorization_url
        assert "github.com" in config.token_url
        assert "api.github.com" in config.user_info_url
        assert "user:email" in config.scope
    
    def test_setup_facebook_oauth2(self):
        """Test Facebook OAuth2 provider setup."""
        config = setup_facebook_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "https://app.com/callback"
        assert "facebook.com" in config.authorization_url
        assert "graph.facebook.com" in config.token_url
        assert "graph.facebook.com" in config.user_info_url
        assert "email" in config.scope
    
    def test_setup_microsoft_oauth2(self):
        """Test Microsoft OAuth2 provider setup."""
        config = setup_microsoft_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "https://app.com/callback"
        assert "login.microsoftonline.com" in config.authorization_url
        assert "login.microsoftonline.com" in config.token_url
        assert "graph.microsoft.com" in config.user_info_url
        assert "openid profile email" in config.scope
    
    def test_setup_linkedin_oauth2(self):
        """Test LinkedIn OAuth2 provider setup."""
        config = setup_linkedin_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "https://app.com/callback"
        assert "linkedin.com" in config.authorization_url
        assert "linkedin.com" in config.token_url
        assert "api.linkedin.com" in config.user_info_url
        assert "r_liteprofile r_emailaddress" in config.scope