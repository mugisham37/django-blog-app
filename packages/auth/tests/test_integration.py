"""
Integration tests for the authentication package.

Tests the complete authentication flow including JWT, MFA, OAuth2, and RBAC.
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch

from auth_package import (
    JWTStrategy, JWTConfig, OAuth2Strategy, TOTPProvider, SMSProvider,
    PasswordHasher, RoleBasedPermission, User, UserStatus, AuthProvider,
    default_user_repository, default_role_registry,
    setup_google_oauth2, setup_github_oauth2
)
from auth_package.permissions import Permission, PermissionAction
from auth_package.models import UserProfile


class TestCompleteAuthenticationFlow:
    """Test complete authentication workflow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Clear repositories
        default_user_repository._users.clear()
        default_user_repository._email_index.clear()
        default_user_repository._username_index.clear()
        
        # Setup JWT
        self.jwt_config = JWTConfig(
            secret_key="test-secret-key",
            access_token_lifetime=timedelta(minutes=15),
            refresh_token_lifetime=timedelta(days=7)
        )
        self.jwt_strategy = JWTStrategy(self.jwt_config)
        
        # Setup password hasher
        self.password_hasher = PasswordHasher()
        
        # Setup RBAC
        self.rbac = RoleBasedPermission(default_role_registry)
        
        # Create test user
        password_hash = self.password_hasher.hash_password("SecurePass123!")
        
        self.test_user = User(
            id="test_user_123",
            username="testuser",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL,
            profile=UserProfile(
                first_name="Test",
                last_name="User",
                display_name="Test User"
            )
        )
        self.test_user.security.password_hash = password_hash
        self.test_user.add_role("user")
        
        default_user_repository.create_user(self.test_user)
    
    def test_complete_jwt_authentication_flow(self):
        """Test complete JWT authentication workflow."""
        # 1. Generate tokens
        tokens = self.jwt_strategy.generate_tokens(
            self.test_user.id,
            {
                "email": self.test_user.email,
                "roles": list(self.test_user.roles)
            }
        )
        
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.expires_in > 0
        
        # 2. Validate access token
        payload = self.jwt_strategy.validate_token(tokens.access_token, "access")
        assert payload["user_id"] == self.test_user.id
        assert payload["email"] == self.test_user.email
        assert "user" in payload["roles"]
        
        # 3. Refresh access token
        new_tokens = self.jwt_strategy.refresh_access_token(tokens.refresh_token)
        assert new_tokens.access_token != tokens.access_token
        assert new_tokens.refresh_token != tokens.refresh_token
        
        # 4. Revoke tokens
        revoked = self.jwt_strategy.revoke_refresh_token(tokens.refresh_token)
        assert revoked is True
        
        # 5. Try to use revoked token (should fail)
        with pytest.raises(Exception):
            self.jwt_strategy.refresh_access_token(tokens.refresh_token)
    
    def test_complete_mfa_flow(self):
        """Test complete MFA workflow."""
        totp_provider = TOTPProvider({"issuer_name": "Test App"})
        
        # 1. Setup TOTP for user
        setup_data = totp_provider.setup_user_totp(
            self.test_user.id,
            self.test_user.email
        )
        
        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "setup_instructions" in setup_data
        
        # 2. Generate challenge
        challenge_result = totp_provider.generate_challenge(
            self.test_user.id,
            setup_data["secret"]
        )
        
        assert challenge_result.success
        assert challenge_result.challenge_id
        
        # 3. Simulate TOTP code generation (mock for testing)
        import pyotp
        totp = pyotp.TOTP(setup_data["secret"])
        current_code = totp.now()
        
        # 4. Verify challenge
        verify_result = totp_provider.verify_challenge(
            challenge_result.challenge_id,
            current_code
        )
        
        assert verify_result.success
        assert "verified successfully" in verify_result.message.lower()
    
    @patch('requests.post')
    @patch('requests.get')
    def test_complete_oauth2_flow(self, mock_get, mock_post):
        """Test complete OAuth2 workflow."""
        # Setup mocks
        mock_post.return_value.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value.raise_for_status.return_value = None
        
        mock_get.return_value.json.return_value = {
            "id": "google_user_123",
            "email": "user@gmail.com",
            "name": "Google User",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_get.return_value.raise_for_status.return_value = None
        
        # Setup OAuth2
        oauth2 = OAuth2Strategy()
        
        google_config = setup_google_oauth2(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://app.com/callback"
        )
        oauth2.register_provider("google", google_config)
        
        # 1. Generate authorization URL
        auth_url = oauth2.get_authorization_url("google", "test_state")
        assert "accounts.google.com" in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "state=test_state" in auth_url
        
        # 2. Exchange code for token
        token_data = oauth2.exchange_code_for_token("google", "auth_code")
        assert token_data["access_token"] == "test_access_token"
        
        # 3. Get user info
        user_info = oauth2.get_user_info("google", "test_access_token")
        assert user_info["email"] == "user@gmail.com"
        assert user_info["name"] == "Google User"
        
        # 4. Create or update user based on OAuth2 data
        oauth_user = User(
            id=f"google_{user_info['id']}",
            username=user_info["email"].split("@")[0],
            email=user_info["email"],
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.GOOGLE,
            external_id=user_info["id"]
        )
        oauth_user.profile.display_name = user_info["name"]
        oauth_user.add_role("user")
        
        default_user_repository.create_user(oauth_user)
        
        # 5. Generate JWT for OAuth user
        oauth_tokens = self.jwt_strategy.generate_tokens(
            oauth_user.id,
            {
                "email": oauth_user.email,
                "auth_provider": oauth_user.auth_provider.value,
                "roles": list(oauth_user.roles)
            }
        )
        
        assert oauth_tokens.access_token
        
        # Verify OAuth user token
        payload = self.jwt_strategy.validate_token(oauth_tokens.access_token)
        assert payload["user_id"] == oauth_user.id
        assert payload["auth_provider"] == "google"
    
    def test_complete_rbac_flow(self):
        """Test complete RBAC workflow."""
        # 1. Create custom permissions
        blog_create = Permission(
            "blog.create",
            PermissionAction.CREATE,
            "blog",
            description="Create blog posts"
        )
        
        blog_edit_own = Permission(
            "blog.edit_own",
            PermissionAction.UPDATE,
            "blog",
            conditions={"owner_id": {"operator": "eq", "value": "user_id"}},
            description="Edit own blog posts"
        )
        
        blog_delete_any = Permission(
            "blog.delete_any",
            PermissionAction.DELETE,
            "blog",
            description="Delete any blog post"
        )
        
        # 2. Register permissions
        default_role_registry.register_permission(blog_create)
        default_role_registry.register_permission(blog_edit_own)
        default_role_registry.register_permission(blog_delete_any)
        
        # 3. Create custom roles
        blogger_role = default_role_registry.create_role(
            "blogger",
            "Blog content creator"
        )
        blogger_role.add_permission(blog_create)
        blogger_role.add_permission(blog_edit_own)
        
        editor_role = default_role_registry.create_role(
            "editor",
            "Content editor",
            parent_roles=["blogger"]
        )
        editor_role.add_permission(blog_delete_any)
        
        # 4. Assign roles to users
        self.test_user.add_role("blogger")
        default_user_repository.update_user(self.test_user)
        
        # Create editor user
        editor_user = User(
            id="editor_123",
            username="editor",
            email="editor@example.com",
            status=UserStatus.ACTIVE
        )
        editor_user.add_role("editor")
        default_user_repository.create_user(editor_user)
        
        # 5. Test permissions
        # Blogger can create posts
        can_create = self.rbac.check_permission(
            ["blogger"],
            "blog",
            PermissionAction.CREATE
        )
        assert can_create is True
        
        # Blogger can edit own posts
        can_edit_own = self.rbac.check_permission(
            ["blogger"],
            "blog",
            PermissionAction.UPDATE,
            {"owner_id": self.test_user.id, "user_id": self.test_user.id}
        )
        assert can_edit_own is True
        
        # Blogger cannot edit others' posts
        can_edit_others = self.rbac.check_permission(
            ["blogger"],
            "blog",
            PermissionAction.UPDATE,
            {"owner_id": "other_user", "user_id": self.test_user.id}
        )
        assert can_edit_others is False
        
        # Blogger cannot delete posts
        can_delete = self.rbac.check_permission(
            ["blogger"],
            "blog",
            PermissionAction.DELETE
        )
        assert can_delete is False
        
        # Editor inherits blogger permissions and can delete
        editor_permissions = self.rbac.get_user_permissions(["editor"])
        permission_names = {p.name for p in editor_permissions}
        
        assert "blog.create" in permission_names
        assert "blog.edit_own" in permission_names
        assert "blog.delete_any" in permission_names
        
        # Editor can delete any post
        can_delete_any = self.rbac.check_permission(
            ["editor"],
            "blog",
            PermissionAction.DELETE
        )
        assert can_delete_any is True
    
    def test_password_security_flow(self):
        """Test password security workflow."""
        # 1. Test password validation
        weak_password = "123456"
        validation = self.password_hasher.validate_password_strength(
            weak_password,
            {"username": self.test_user.username, "email": self.test_user.email}
        )
        
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert validation["score"] < 3
        
        # 2. Test strong password
        strong_password = "MyVerySecureP@ssw0rd2024!"
        validation = self.password_hasher.validate_password_strength(
            strong_password,
            {"username": self.test_user.username, "email": self.test_user.email}
        )
        
        assert validation["valid"] is True
        assert validation["score"] >= 4
        
        # 3. Test password hashing and verification
        password_hash = self.password_hasher.hash_password(strong_password)
        assert password_hash != strong_password
        
        # Correct password
        is_valid = self.password_hasher.verify_password(strong_password, password_hash)
        assert is_valid is True
        
        # Wrong password
        is_invalid = self.password_hasher.verify_password("wrong_password", password_hash)
        assert is_invalid is False
    
    def test_user_lifecycle_flow(self):
        """Test complete user lifecycle."""
        # 1. Create user with pending verification
        new_user = User(
            id="new_user_123",
            username="newuser",
            email="newuser@example.com",
            status=UserStatus.PENDING_VERIFICATION
        )
        
        default_user_repository.create_user(new_user)
        
        # 2. User is not active initially
        assert new_user.is_active is False
        
        # 3. Verify email
        new_user.verify_email()
        assert new_user.email_verified is True
        assert new_user.status == UserStatus.ACTIVE
        assert new_user.is_active is True
        
        # 4. Add roles
        new_user.add_role("user")
        default_user_repository.update_user(new_user)
        
        # 5. Test account security
        # Simulate failed login attempts
        new_user.security.record_failed_login(max_attempts=3)
        new_user.security.record_failed_login(max_attempts=3)
        new_user.security.record_failed_login(max_attempts=3)
        
        assert new_user.security.is_locked() is True
        assert new_user.is_active is False  # Locked account is not active
        
        # 6. Unlock account
        new_user.security.unlock_account()
        assert new_user.security.is_locked() is False
        assert new_user.is_active is True
        
        # 7. Successful login
        new_user.security.record_successful_login("192.168.1.1")
        assert new_user.security.failed_login_attempts == 0
        assert new_user.security.last_login_ip == "192.168.1.1"
        
        # 8. Suspend user
        new_user.suspend()
        assert new_user.status == UserStatus.SUSPENDED
        assert new_user.is_active is False
        
        # 9. Reactivate user
        new_user.activate()
        assert new_user.status == UserStatus.ACTIVE
        assert new_user.is_active is True


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_jwt_tokens(self):
        """Test handling of invalid JWT tokens."""
        jwt_config = JWTConfig(secret_key="test-key")
        jwt_strategy = JWTStrategy(jwt_config)
        
        # Invalid token format
        with pytest.raises(Exception):
            jwt_strategy.validate_token("invalid.token.format")
        
        # Expired token (mock)
        with pytest.raises(Exception):
            jwt_strategy.validate_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDk0NTkyMDB9.invalid")
    
    def test_mfa_rate_limiting(self):
        """Test MFA rate limiting."""
        sms_provider = SMSProvider({
            "provider": "custom",  # Use custom provider for testing
            "rate_limit": 2  # Very low limit for testing
        })
        
        user_id = "rate_limit_test"
        phone = "+1234567890"
        
        # First request should succeed
        result1 = sms_provider.generate_challenge(user_id, phone)
        assert result1.success is True
        
        # Second request should succeed
        result2 = sms_provider.generate_challenge(user_id, phone)
        assert result2.success is True
        
        # Third request should fail due to rate limit
        result3 = sms_provider.generate_challenge(user_id, phone)
        assert result3.success is False
        assert "rate limit" in result3.message.lower()
    
    def test_rbac_edge_cases(self):
        """Test RBAC edge cases."""
        rbac = RoleBasedPermission(default_role_registry)
        
        # Empty roles
        can_access = rbac.check_permission([], "blog", PermissionAction.READ)
        assert can_access is False
        
        # Non-existent role
        can_access = rbac.check_permission(["nonexistent"], "blog", PermissionAction.READ)
        assert can_access is False
        
        # Non-existent resource
        can_access = rbac.check_permission(["user"], "nonexistent", PermissionAction.READ)
        assert can_access is False
    
    def test_user_repository_constraints(self):
        """Test user repository constraints."""
        # Duplicate username
        user1 = User(id="1", username="duplicate", email="user1@example.com")
        user2 = User(id="2", username="duplicate", email="user2@example.com")
        
        default_user_repository.create_user(user1)
        
        with pytest.raises(ValueError, match="username.*already exists"):
            default_user_repository.create_user(user2)
        
        # Duplicate email
        user3 = User(id="3", username="unique", email="user1@example.com")
        
        with pytest.raises(ValueError, match="email.*already exists"):
            default_user_repository.create_user(user3)


class TestPerformance:
    """Test performance characteristics."""
    
    def test_password_hashing_performance(self):
        """Test password hashing performance."""
        import time
        
        hasher = PasswordHasher(rounds=4)  # Lower rounds for testing
        password = "TestPassword123!"
        
        # Hash password
        start_time = time.time()
        password_hash = hasher.hash_password(password)
        hash_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust as needed)
        assert hash_time < 1.0  # 1 second max for low rounds
        
        # Verify password
        start_time = time.time()
        is_valid = hasher.verify_password(password, password_hash)
        verify_time = time.time() - start_time
        
        assert is_valid is True
        assert verify_time < 1.0  # 1 second max for verification
    
    def test_jwt_token_performance(self):
        """Test JWT token generation and validation performance."""
        import time
        
        jwt_config = JWTConfig(secret_key="performance-test-key")
        jwt_strategy = JWTStrategy(jwt_config)
        
        # Generate multiple tokens
        start_time = time.time()
        tokens = []
        
        for i in range(100):
            token_pair = jwt_strategy.generate_tokens(f"user_{i}")
            tokens.append(token_pair)
        
        generation_time = time.time() - start_time
        
        # Should generate 100 tokens quickly
        assert generation_time < 1.0  # 1 second for 100 tokens
        
        # Validate tokens
        start_time = time.time()
        
        for token_pair in tokens:
            payload = jwt_strategy.validate_token(token_pair.access_token)
            assert payload is not None
        
        validation_time = time.time() - start_time
        
        # Should validate 100 tokens quickly
        assert validation_time < 1.0  # 1 second for 100 validations