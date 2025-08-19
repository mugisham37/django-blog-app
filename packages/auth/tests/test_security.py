"""
Tests for security utilities (password hashing and token management).
"""

import pytest
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import patch

from auth_package.security import PasswordHasher, PasswordPolicy, TokenManager


class TestPasswordHasher:
    """Test password hashing functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.hasher = PasswordHasher(rounds=4)  # Low rounds for faster tests
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = self.hasher.hash_password(password)
        
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password_123"
        hashed = self.hasher.hash_password(password)
        
        assert self.hasher.verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = self.hasher.hash_password(password)
        
        assert self.hasher.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_invalid_input(self):
        """Test password verification with invalid input."""
        assert self.hasher.verify_password(None, "hash") is False
        assert self.hasher.verify_password("password", None) is False
        assert self.hasher.verify_password(123, "hash") is False
    
    def test_hash_password_invalid_input(self):
        """Test password hashing with invalid input."""
        with pytest.raises(TypeError):
            self.hasher.hash_password(None)
        
        with pytest.raises(TypeError):
            self.hasher.hash_password(123)
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation for valid password."""
        password = "StrongP@ssw0rd123"
        result = self.hasher.validate_password_strength(password)
        
        assert result["valid"] is True
        assert result["score"] >= 4
        assert len(result["errors"]) == 0
        assert result["strength"] in ["Strong", "Very Strong"]
    
    def test_validate_password_strength_weak(self):
        """Test password strength validation for weak password."""
        password = "weak"
        result = self.hasher.validate_password_strength(password)
        
        assert result["valid"] is False
        assert result["score"] < 3
        assert len(result["errors"]) > 0
        assert "at least 8 characters" in str(result["errors"])
    
    def test_validate_password_strength_missing_requirements(self):
        """Test password validation with missing requirements."""
        password = "nouppercase123!"
        result = self.hasher.validate_password_strength(password)
        
        assert result["valid"] is False
        assert any("uppercase" in error for error in result["errors"])
    
    def test_validate_password_strength_common_password(self):
        """Test validation against common passwords."""
        password = "password123"
        result = self.hasher.validate_password_strength(password)
        
        assert result["valid"] is False
        assert any("too common" in error for error in result["errors"])
    
    def test_validate_password_strength_user_info(self):
        """Test validation against user information."""
        password = "john_password_123"
        user_info = {"username": "john", "email": "john@example.com"}
        result = self.hasher.validate_password_strength(password, user_info)
        
        assert result["valid"] is False
        assert any("personal information" in error for error in result["errors"])
    
    def test_validate_password_strength_consecutive_chars(self):
        """Test validation with consecutive characters."""
        password = "Passsssword123!"
        result = self.hasher.validate_password_strength(password)
        
        assert len(result["warnings"]) > 0
        assert any("consecutive" in warning for warning in result["warnings"])
    
    def test_custom_password_policy(self):
        """Test custom password policy."""
        policy = PasswordPolicy(
            min_length=12,
            require_special_chars=False,
            max_consecutive_chars=2
        )
        
        self.hasher.set_policy(policy)
        
        password = "ShortPass1"  # Only 10 chars
        result = self.hasher.validate_password_strength(password)
        
        assert result["valid"] is False
        assert any("12 characters" in error for error in result["errors"])
    
    def test_bcrypt_rounds_validation(self):
        """Test bcrypt rounds validation."""
        # Valid rounds
        hasher = PasswordHasher(rounds=10)
        assert hasher.rounds == 10
        
        # Invalid rounds
        with pytest.raises(ValueError):
            PasswordHasher(rounds=3)  # Too low
        
        with pytest.raises(ValueError):
            PasswordHasher(rounds=32)  # Too high


class TestTokenManager:
    """Test token management functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.token_manager = TokenManager("test-secret-key")
    
    def test_generate_token(self):
        """Test token generation."""
        user_id = "user123"
        token_type = "reset"
        metadata = {"email": "user@example.com"}
        
        token = self.token_manager.generate_token(
            user_id, token_type, expires_in=3600, metadata=metadata
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_token_success(self):
        """Test successful token validation."""
        user_id = "user123"
        token_type = "reset"
        metadata = {"email": "user@example.com"}
        
        token = self.token_manager.generate_token(
            user_id, token_type, metadata=metadata
        )
        
        token_data = self.token_manager.validate_token(token, token_type)
        
        assert token_data is not None
        assert token_data["user_id"] == user_id
        assert token_data["token_type"] == token_type
        assert token_data["metadata"] == metadata
    
    def test_validate_token_invalid(self):
        """Test validation of invalid token."""
        result = self.token_manager.validate_token("invalid_token")
        assert result is None
    
    def test_validate_token_wrong_type(self):
        """Test validation with wrong token type."""
        token = self.token_manager.generate_token("user123", "reset")
        result = self.token_manager.validate_token(token, "verify")
        
        assert result is None
    
    def test_validate_token_expired(self):
        """Test validation of expired token."""
        token = self.token_manager.generate_token(
            "user123", "reset", expires_in=-1  # Already expired
        )
        
        result = self.token_manager.validate_token(token)
        assert result is None
    
    def test_use_token(self):
        """Test one-time token usage."""
        token = self.token_manager.generate_token("user123", "reset")
        
        # First use should succeed
        assert self.token_manager.use_token(token) is True
        
        # Second use should fail
        assert self.token_manager.use_token(token) is False
        
        # Validation should also fail after use
        assert self.token_manager.validate_token(token) is None
    
    def test_revoke_token(self):
        """Test token revocation."""
        token = self.token_manager.generate_token("user123", "reset")
        
        # Token should be valid initially
        assert self.token_manager.validate_token(token) is not None
        
        # Revoke token
        assert self.token_manager.revoke_token(token) is True
        
        # Token should be invalid after revocation
        assert self.token_manager.validate_token(token) is None
    
    def test_revoke_user_tokens(self):
        """Test revoking all tokens for a user."""
        user_id = "user123"
        
        # Generate multiple tokens
        token1 = self.token_manager.generate_token(user_id, "reset")
        token2 = self.token_manager.generate_token(user_id, "verify")
        token3 = self.token_manager.generate_token("other_user", "reset")
        
        # Revoke all tokens for user123
        revoked_count = self.token_manager.revoke_user_tokens(user_id)
        assert revoked_count == 2
        
        # user123 tokens should be invalid
        assert self.token_manager.validate_token(token1) is None
        assert self.token_manager.validate_token(token2) is None
        
        # Other user's token should still be valid
        assert self.token_manager.validate_token(token3) is not None
    
    def test_revoke_user_tokens_by_type(self):
        """Test revoking user tokens by type."""
        user_id = "user123"
        
        # Generate tokens of different types
        reset_token = self.token_manager.generate_token(user_id, "reset")
        verify_token = self.token_manager.generate_token(user_id, "verify")
        
        # Revoke only reset tokens
        revoked_count = self.token_manager.revoke_user_tokens(user_id, "reset")
        assert revoked_count == 1
        
        # Reset token should be invalid
        assert self.token_manager.validate_token(reset_token) is None
        
        # Verify token should still be valid
        assert self.token_manager.validate_token(verify_token) is not None
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Generate expired token
        expired_token = self.token_manager.generate_token(
            "user123", "reset", expires_in=-3600  # Expired 1 hour ago
        )
        
        # Generate valid token
        valid_token = self.token_manager.generate_token(
            "user456", "reset", expires_in=3600
        )
        
        # Cleanup expired tokens
        self.token_manager.cleanup_expired_tokens()
        
        # Expired token should be removed from storage
        # Valid token should still exist
        assert self.token_manager.validate_token(valid_token) is not None
    
    def test_generate_secure_random_string(self):
        """Test secure random string generation."""
        random_string = self.token_manager.generate_secure_random_string(32)
        
        assert isinstance(random_string, str)
        assert len(random_string) > 0
        
        # Generate another string to ensure they're different
        another_string = self.token_manager.generate_secure_random_string(32)
        assert random_string != another_string
    
    def test_generate_numeric_code(self):
        """Test numeric code generation."""
        code = self.token_manager.generate_numeric_code(6)
        
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()
        
        # Generate another code to ensure they're different
        another_code = self.token_manager.generate_numeric_code(6)
        assert code != another_code
    
    def test_constant_time_compare(self):
        """Test constant-time string comparison."""
        string1 = "test_string"
        string2 = "test_string"
        string3 = "different_string"
        
        assert self.token_manager.constant_time_compare(string1, string2) is True
        assert self.token_manager.constant_time_compare(string1, string3) is False
    
    def test_token_manager_without_secret(self):
        """Test token manager without provided secret key."""
        manager = TokenManager()  # No secret key provided
        
        # Should still work with auto-generated key
        token = manager.generate_token("user123", "test")
        assert isinstance(token, str)
        
        # Should be able to validate own tokens
        token_data = manager.validate_token(token)
        assert token_data is not None


class TestPasswordPolicy:
    """Test password policy configuration."""
    
    def test_default_policy(self):
        """Test default password policy values."""
        policy = PasswordPolicy()
        
        assert policy.min_length == 8
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digits is True
        assert policy.require_special_chars is True
        assert policy.max_consecutive_chars == 3
        assert policy.prevent_common_passwords is True
        assert policy.prevent_user_info is True
    
    def test_custom_policy(self):
        """Test custom password policy values."""
        policy = PasswordPolicy(
            min_length=12,
            max_length=64,
            require_uppercase=False,
            require_special_chars=False,
            max_consecutive_chars=2,
            prevent_common_passwords=False
        )
        
        assert policy.min_length == 12
        assert policy.max_length == 64
        assert policy.require_uppercase is False
        assert policy.require_special_chars is False
        assert policy.max_consecutive_chars == 2
        assert policy.prevent_common_passwords is False