"""
Authentication strategies for JWT and OAuth2 implementations.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


@dataclass
class TokenPair:
    """Container for access and refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


@dataclass
class JWTConfig:
    """JWT configuration settings."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_lifetime: timedelta = timedelta(minutes=15)
    refresh_token_lifetime: timedelta = timedelta(days=7)
    issuer: str = "auth-package"
    audience: str = "api"


class JWTStrategy:
    """
    JWT authentication strategy with refresh token mechanism.
    
    Provides secure JWT token generation, validation, and refresh capabilities
    with configurable expiration times and security settings.
    """
    
    def __init__(self, config: JWTConfig):
        self.config = config
        self._refresh_tokens = {}  # In production, use Redis or database
    
    def generate_tokens(self, user_id: Union[str, int], user_data: Dict[str, Any] = None) -> TokenPair:
        """
        Generate access and refresh token pair for a user.
        
        Args:
            user_id: Unique user identifier
            user_data: Additional user data to include in token payload
            
        Returns:
            TokenPair containing access and refresh tokens
        """
        now = datetime.utcnow()
        user_data = user_data or {}
        
        # Generate access token
        access_payload = {
            "user_id": user_id,
            "iat": now,
            "exp": now + self.config.access_token_lifetime,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "access",
            **user_data
        }
        
        access_token = jwt.encode(
            access_payload,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
        
        # Generate refresh token
        refresh_token_id = secrets.token_urlsafe(32)
        refresh_payload = {
            "user_id": user_id,
            "token_id": refresh_token_id,
            "iat": now,
            "exp": now + self.config.refresh_token_lifetime,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "refresh"
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
        
        # Store refresh token metadata
        self._refresh_tokens[refresh_token_id] = {
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + self.config.refresh_token_lifetime,
            "is_active": True
        }
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self.config.access_token_lifetime.total_seconds()),
            token_type="Bearer"
        )
    
    def validate_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Validate and decode a JWT token.
        
        Args:
            token: JWT token to validate
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer
            )
            
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError(f"Invalid token type. Expected {token_type}")
            
            # Additional validation for refresh tokens
            if token_type == "refresh":
                token_id = payload.get("token_id")
                if not token_id or token_id not in self._refresh_tokens:
                    raise jwt.InvalidTokenError("Refresh token not found")
                
                token_meta = self._refresh_tokens[token_id]
                if not token_meta["is_active"]:
                    raise jwt.InvalidTokenError("Refresh token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise
    
    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenPair with fresh access token
            
        Raises:
            jwt.InvalidTokenError: If refresh token is invalid
        """
        payload = self.validate_token(refresh_token, "refresh")
        user_id = payload["user_id"]
        
        # Generate new token pair
        return self.generate_tokens(user_id)
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if token was successfully revoked
        """
        try:
            payload = self.validate_token(refresh_token, "refresh")
            token_id = payload["token_id"]
            
            if token_id in self._refresh_tokens:
                self._refresh_tokens[token_id]["is_active"] = False
                return True
                
        except jwt.InvalidTokenError:
            pass
        
        return False
    
    def revoke_all_user_tokens(self, user_id: Union[str, int]) -> int:
        """
        Revoke all refresh tokens for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of tokens revoked
        """
        revoked_count = 0
        for token_id, token_meta in self._refresh_tokens.items():
            if token_meta["user_id"] == user_id and token_meta["is_active"]:
                token_meta["is_active"] = False
                revoked_count += 1
        
        return revoked_count


class OAuth2Strategy:
    """
    OAuth2 authentication strategy for social login providers.
    
    Supports multiple OAuth2 providers with configurable settings
    and secure token exchange mechanisms.
    """
    
    @dataclass
    class ProviderConfig:
        """OAuth2 provider configuration."""
        client_id: str
        client_secret: str
        authorization_url: str
        token_url: str
        user_info_url: str
        scope: str = "openid profile email"
        redirect_uri: str = ""
    
    def __init__(self):
        self.providers = {}
    
    def register_provider(self, name: str, config: ProviderConfig):
        """
        Register an OAuth2 provider.
        
        Args:
            name: Provider name (e.g., "google", "github")
            config: Provider configuration
        """
        self.providers[name] = config
    
    def get_authorization_url(self, provider: str, state: str = None) -> str:
        """
        Generate authorization URL for OAuth2 flow.
        
        Args:
            provider: Provider name
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.providers[provider]
        state = state or secrets.token_urlsafe(32)
        
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": config.scope,
            "response_type": "code",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{config.authorization_url}?{query_string}"
    
    def exchange_code_for_token(self, provider: str, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            provider: Provider name
            code: Authorization code from OAuth2 callback
            
        Returns:
            Token response from provider
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.providers[provider]
        
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config.redirect_uri
        }
        
        response = requests.post(config.token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """
        Fetch user information using access token.
        
        Args:
            provider: Provider name
            access_token: OAuth2 access token
            
        Returns:
            User information from provider
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.providers[provider]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(config.user_info_url, headers=headers)
        response.raise_for_status()
        
        return response.json()


# Pre-configured OAuth2 providers
def setup_google_oauth2(client_id: str, client_secret: str, redirect_uri: str) -> OAuth2Strategy.ProviderConfig:
    """Setup Google OAuth2 provider configuration."""
    return OAuth2Strategy.ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scope="openid profile email",
        redirect_uri=redirect_uri
    )


def setup_github_oauth2(client_id: str, client_secret: str, redirect_uri: str) -> OAuth2Strategy.ProviderConfig:
    """Setup GitHub OAuth2 provider configuration."""
    return OAuth2Strategy.ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        user_info_url="https://api.github.com/user",
        scope="user:email",
        redirect_uri=redirect_uri
    )


def setup_facebook_oauth2(client_id: str, client_secret: str, redirect_uri: str) -> OAuth2Strategy.ProviderConfig:
    """Setup Facebook OAuth2 provider configuration."""
    return OAuth2Strategy.ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorization_url="https://www.facebook.com/v18.0/dialog/oauth",
        token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        user_info_url="https://graph.facebook.com/v18.0/me?fields=id,name,email",
        scope="email",
        redirect_uri=redirect_uri
    )


def setup_microsoft_oauth2(client_id: str, client_secret: str, redirect_uri: str) -> OAuth2Strategy.ProviderConfig:
    """Setup Microsoft OAuth2 provider configuration."""
    return OAuth2Strategy.ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        user_info_url="https://graph.microsoft.com/v1.0/me",
        scope="openid profile email",
        redirect_uri=redirect_uri
    )


def setup_linkedin_oauth2(client_id: str, client_secret: str, redirect_uri: str) -> OAuth2Strategy.ProviderConfig:
    """Setup LinkedIn OAuth2 provider configuration."""
    return OAuth2Strategy.ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorization_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        user_info_url="https://api.linkedin.com/v2/people/~:(id,firstName,lastName,emailAddress)",
        scope="r_liteprofile r_emailaddress",
        redirect_uri=redirect_uri
    )