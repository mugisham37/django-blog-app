"""
Security utilities for password hashing and token management.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


@dataclass
class PasswordPolicy:
    """Password policy configuration."""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    max_consecutive_chars: int = 3
    prevent_common_passwords: bool = True
    prevent_user_info: bool = True


class PasswordHasher:
    """
    Secure password hashing using bcrypt with configurable rounds.
    
    Provides password hashing, verification, and strength validation
    with enterprise-grade security standards.
    """
    
    def __init__(self, rounds: int = 12):
        """
        Initialize password hasher.
        
        Args:
            rounds: bcrypt rounds (4-31, default 12)
        """
        if not 4 <= rounds <= 31:
            raise ValueError("bcrypt rounds must be between 4 and 31")
        
        self.rounds = rounds
        self.policy = PasswordPolicy()
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches hash
        """
        if not isinstance(password, str) or not isinstance(hashed_password, str):
            return False
        
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    def validate_password_strength(self, password: str, user_info: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Validate password against security policy.
        
        Args:
            password: Password to validate
            user_info: User information to check against (username, email, etc.)
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        score = 0
        
        if not password:
            return {
                "valid": False,
                "score": 0,
                "errors": ["Password is required"],
                "warnings": []
            }
        
        # Length checks
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")
        elif len(password) >= self.policy.min_length:
            score += 1
        
        if len(password) > self.policy.max_length:
            errors.append(f"Password must not exceed {self.policy.max_length} characters")
        
        # Character type checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in self.policy.special_chars for c in password)
        
        if self.policy.require_uppercase and not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        elif has_upper:
            score += 1
        
        if self.policy.require_lowercase and not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        elif has_lower:
            score += 1
        
        if self.policy.require_digits and not has_digit:
            errors.append("Password must contain at least one digit")
        elif has_digit:
            score += 1
        
        if self.policy.require_special_chars and not has_special:
            errors.append(f"Password must contain at least one special character: {self.policy.special_chars}")
        elif has_special:
            score += 1
        
        # Consecutive character check
        consecutive_count = 1
        max_consecutive = 1
        
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1
        
        if max_consecutive > self.policy.max_consecutive_chars:
            warnings.append(f"Password contains {max_consecutive} consecutive identical characters")
        
        # Common password check
        if self.policy.prevent_common_passwords:
            if self._is_common_password(password):
                errors.append("Password is too common. Please choose a more unique password")
        
        # User info check
        if self.policy.prevent_user_info and user_info:
            if self._contains_user_info(password, user_info):
                errors.append("Password must not contain personal information")
        
        # Calculate strength score (0-5)
        strength_score = min(5, score + (1 if len(password) >= 12 else 0))
        
        return {
            "valid": len(errors) == 0,
            "score": strength_score,
            "errors": errors,
            "warnings": warnings,
            "strength": self._get_strength_label(strength_score)
        }
    
    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list."""
        # Common passwords list (simplified)
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890", "password1",
            "123456789", "12345678", "12345", "1234", "111111"
        }
        
        return password.lower() in common_passwords
    
    def _contains_user_info(self, password: str, user_info: Dict[str, str]) -> bool:
        """Check if password contains user information."""
        password_lower = password.lower()
        
        for key, value in user_info.items():
            if value and len(value) >= 3:
                if value.lower() in password_lower:
                    return True
        
        return False
    
    def _get_strength_label(self, score: int) -> str:
        """Get strength label from score."""
        labels = {
            0: "Very Weak",
            1: "Weak", 
            2: "Fair",
            3: "Good",
            4: "Strong",
            5: "Very Strong"
        }
        return labels.get(score, "Unknown")
    
    def set_policy(self, policy: PasswordPolicy):
        """Set password policy."""
        self.policy = policy


class TokenManager:
    """
    Secure token management for various authentication purposes.
    
    Provides token generation, validation, and encryption for
    password resets, email verification, and other security tokens.
    """
    
    def __init__(self, secret_key: str = None):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for token encryption (auto-generated if not provided)
        """
        if secret_key:
            # Derive key from secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'stable_salt',  # Use consistent salt for key derivation
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        else:
            # Generate random key
            key = Fernet.generate_key()
        
        self.cipher = Fernet(key)
        self._tokens = {}  # In production, use Redis or database
    
    def generate_token(self, 
                      user_id: Union[str, int], 
                      token_type: str, 
                      expires_in: int = 3600,
                      metadata: Dict[str, Any] = None) -> str:
        """
        Generate encrypted token.
        
        Args:
            user_id: User identifier
            token_type: Type of token (reset, verify, etc.)
            expires_in: Token lifetime in seconds
            metadata: Additional token data
            
        Returns:
            Encrypted token string
        """
        token_id = secrets.token_urlsafe(32)
        
        token_data = {
            "token_id": token_id,
            "user_id": str(user_id),
            "token_type": token_type,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "metadata": metadata or {}
        }
        
        # Encrypt token data
        token_json = str(token_data).encode('utf-8')
        encrypted_token = self.cipher.encrypt(token_json)
        
        # Store token metadata
        self._tokens[token_id] = {
            "user_id": str(user_id),
            "token_type": token_type,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
            "is_used": False
        }
        
        return base64.urlsafe_b64encode(encrypted_token).decode('utf-8')
    
    def validate_token(self, token: str, token_type: str = None) -> Dict[str, Any]:
        """
        Validate and decrypt token.
        
        Args:
            token: Encrypted token string
            token_type: Expected token type (optional)
            
        Returns:
            Token data if valid, None if invalid
        """
        try:
            # Decode and decrypt token
            encrypted_token = base64.urlsafe_b64decode(token.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_token)
            token_data = eval(decrypted_data.decode('utf-8'))
            
            token_id = token_data["token_id"]
            
            # Check if token exists and is not used
            if token_id not in self._tokens:
                return None
            
            token_meta = self._tokens[token_id]
            
            if token_meta["is_used"]:
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                return None
            
            # Check token type if specified
            if token_type and token_data["token_type"] != token_type:
                return None
            
            return token_data
            
        except Exception:
            return None
    
    def use_token(self, token: str) -> bool:
        """
        Mark token as used (one-time use).
        
        Args:
            token: Token to mark as used
            
        Returns:
            True if token was successfully marked as used
        """
        token_data = self.validate_token(token)
        
        if token_data:
            token_id = token_data["token_id"]
            if token_id in self._tokens:
                self._tokens[token_id]["is_used"] = True
                return True
        
        return False
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if token was revoked
        """
        token_data = self.validate_token(token)
        
        if token_data:
            token_id = token_data["token_id"]
            if token_id in self._tokens:
                del self._tokens[token_id]
                return True
        
        return False
    
    def revoke_user_tokens(self, user_id: Union[str, int], token_type: str = None) -> int:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User identifier
            token_type: Optional token type filter
            
        Returns:
            Number of tokens revoked
        """
        user_id_str = str(user_id)
        revoked_count = 0
        
        tokens_to_remove = []
        
        for token_id, token_meta in self._tokens.items():
            if token_meta["user_id"] == user_id_str:
                if token_type is None or token_meta["token_type"] == token_type:
                    tokens_to_remove.append(token_id)
                    revoked_count += 1
        
        for token_id in tokens_to_remove:
            del self._tokens[token_id]
        
        return revoked_count
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens."""
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token_id, token_meta in self._tokens.items():
            if token_meta["expires_at"] < current_time:
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            del self._tokens[token_id]
    
    def generate_secure_random_string(self, length: int = 32) -> str:
        """Generate cryptographically secure random string."""
        return secrets.token_urlsafe(length)
    
    def generate_numeric_code(self, length: int = 6) -> str:
        """Generate numeric verification code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))