"""
Advanced password policies and account lockout mechanisms.
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class PasswordStrength(Enum):
    """Password strength levels."""
    VERY_WEAK = 0
    WEAK = 1
    FAIR = 2
    GOOD = 3
    STRONG = 4
    VERY_STRONG = 5


class LockoutReason(Enum):
    """Account lockout reasons."""
    FAILED_ATTEMPTS = "failed_attempts"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ADMIN_LOCK = "admin_lock"
    SECURITY_VIOLATION = "security_violation"
    BRUTE_FORCE = "brute_force"


@dataclass
class PasswordPolicy:
    """Advanced password policy configuration."""
    # Length requirements
    min_length: int = 8
    max_length: int = 128
    
    # Character requirements
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Pattern restrictions
    max_consecutive_chars: int = 3
    max_repeated_chars: int = 2
    prevent_keyboard_patterns: bool = True
    prevent_dictionary_words: bool = True
    
    # History and reuse
    prevent_reuse_count: int = 5
    prevent_user_info: bool = True
    
    # Complexity scoring
    min_complexity_score: int = 3
    bonus_length_threshold: int = 12
    bonus_mixed_case: int = 1
    bonus_special_chars: int = 1
    bonus_numbers: int = 1
    
    # Common password lists
    common_passwords_file: Optional[str] = None
    custom_blacklist: List[str] = field(default_factory=list)
    
    # Expiration
    max_age_days: Optional[int] = None
    warn_before_expiry_days: int = 7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_digits": self.require_digits,
            "require_special_chars": self.require_special_chars,
            "special_chars": self.special_chars,
            "max_consecutive_chars": self.max_consecutive_chars,
            "max_repeated_chars": self.max_repeated_chars,
            "prevent_keyboard_patterns": self.prevent_keyboard_patterns,
            "prevent_dictionary_words": self.prevent_dictionary_words,
            "prevent_reuse_count": self.prevent_reuse_count,
            "prevent_user_info": self.prevent_user_info,
            "min_complexity_score": self.min_complexity_score,
            "max_age_days": self.max_age_days,
            "warn_before_expiry_days": self.warn_before_expiry_days
        }


@dataclass
class AccountLockout:
    """Account lockout information."""
    user_id: str
    reason: LockoutReason
    locked_at: datetime
    locked_until: Optional[datetime] = None
    attempt_count: int = 0
    ip_addresses: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return True  # Permanent lock
        return datetime.utcnow() < self.locked_until
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining for lockout."""
        if self.locked_until is None:
            return None
        
        remaining = self.locked_until - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


@dataclass
class LoginAttempt:
    """Login attempt tracking."""
    user_id: str
    ip_address: str
    timestamp: datetime
    success: bool
    user_agent: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class PasswordValidator:
    """
    Advanced password validation with comprehensive policy enforcement.
    
    Provides password strength analysis, policy compliance checking,
    and security recommendations.
    """
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self._common_passwords = self._load_common_passwords()
        self._keyboard_patterns = self._generate_keyboard_patterns()
    
    def validate_password(self, 
                         password: str, 
                         user_info: Dict[str, str] = None,
                         password_history: List[str] = None) -> Dict[str, Any]:
        """
        Comprehensive password validation.
        
        Args:
            password: Password to validate
            user_info: User information for validation
            password_history: Previous password hashes
            
        Returns:
            Validation result with errors, warnings, and strength score
        """
        errors = []
        warnings = []
        suggestions = []
        
        if not password:
            return {
                "valid": False,
                "strength": PasswordStrength.VERY_WEAK,
                "score": 0,
                "errors": ["Password is required"],
                "warnings": [],
                "suggestions": ["Please enter a password"]
            }
        
        # Length validation
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")
        
        if len(password) > self.policy.max_length:
            errors.append(f"Password must not exceed {self.policy.max_length} characters")
        
        # Character type validation
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(f'[{re.escape(self.policy.special_chars)}]', password))
        
        if self.policy.require_uppercase and not has_upper:
            errors.append("Password must contain at least one uppercase letter")
            suggestions.append("Add uppercase letters (A-Z)")
        
        if self.policy.require_lowercase and not has_lower:
            errors.append("Password must contain at least one lowercase letter")
            suggestions.append("Add lowercase letters (a-z)")
        
        if self.policy.require_digits and not has_digit:
            errors.append("Password must contain at least one digit")
            suggestions.append("Add numbers (0-9)")
        
        if self.policy.require_special_chars and not has_special:
            errors.append(f"Password must contain at least one special character: {self.policy.special_chars}")
            suggestions.append("Add special characters (!@#$%^&*)")
        
        # Pattern validation
        consecutive_errors = self._check_consecutive_chars(password)
        if consecutive_errors:
            errors.extend(consecutive_errors)
        
        repeated_errors = self._check_repeated_chars(password)
        if repeated_errors:
            errors.extend(repeated_errors)
        
        if self.policy.prevent_keyboard_patterns:
            keyboard_errors = self._check_keyboard_patterns(password)
            if keyboard_errors:
                errors.extend(keyboard_errors)
        
        # Dictionary and common password checks
        if self.policy.prevent_dictionary_words:
            dictionary_errors = self._check_dictionary_words(password)
            if dictionary_errors:
                errors.extend(dictionary_errors)
        
        common_password_errors = self._check_common_passwords(password)
        if common_password_errors:
            errors.extend(common_password_errors)
        
        # User information checks
        if self.policy.prevent_user_info and user_info:
            user_info_errors = self._check_user_info(password, user_info)
            if user_info_errors:
                errors.extend(user_info_errors)
        
        # Password history checks
        if password_history and self.policy.prevent_reuse_count > 0:
            reuse_errors = self._check_password_reuse(password, password_history)
            if reuse_errors:
                errors.extend(reuse_errors)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(password)
        
        if complexity_score < self.policy.min_complexity_score:
            errors.append(f"Password complexity score ({complexity_score}) is below minimum ({self.policy.min_complexity_score})")
        
        # Determine strength
        strength = self._determine_strength(password, complexity_score)
        
        # Generate suggestions for improvement
        if not suggestions and strength.value < 4:
            suggestions = self._generate_suggestions(password, has_upper, has_lower, has_digit, has_special)
        
        return {
            "valid": len(errors) == 0,
            "strength": strength,
            "score": complexity_score,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def check_password_expiry(self, password_changed_at: datetime) -> Dict[str, Any]:
        """
        Check if password has expired or is about to expire.
        
        Args:
            password_changed_at: When password was last changed
            
        Returns:
            Expiry information
        """
        if not self.policy.max_age_days:
            return {"expired": False, "expires_soon": False}
        
        now = datetime.utcnow()
        age = now - password_changed_at
        max_age = timedelta(days=self.policy.max_age_days)
        
        expired = age >= max_age
        
        # Check if expiring soon
        warn_threshold = timedelta(days=self.policy.warn_before_expiry_days)
        expires_soon = (max_age - age) <= warn_threshold and not expired
        
        days_until_expiry = (max_age - age).days if not expired else 0
        
        return {
            "expired": expired,
            "expires_soon": expires_soon,
            "days_until_expiry": max(0, days_until_expiry),
            "age_days": age.days
        }
    
    def _check_consecutive_chars(self, password: str) -> List[str]:
        """Check for consecutive identical characters."""
        errors = []
        consecutive_count = 1
        max_consecutive = 1
        
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1
        
        if max_consecutive > self.policy.max_consecutive_chars:
            errors.append(f"Password contains {max_consecutive} consecutive identical characters (max allowed: {self.policy.max_consecutive_chars})")
        
        return errors
    
    def _check_repeated_chars(self, password: str) -> List[str]:
        """Check for repeated characters throughout password."""
        errors = []
        char_counts = {}
        
        for char in password:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        max_repeated = max(char_counts.values()) if char_counts else 0
        
        if max_repeated > self.policy.max_repeated_chars:
            errors.append(f"Password contains characters repeated {max_repeated} times (max allowed: {self.policy.max_repeated_chars})")
        
        return errors
    
    def _check_keyboard_patterns(self, password: str) -> List[str]:
        """Check for keyboard patterns."""
        errors = []
        password_lower = password.lower()
        
        for pattern in self._keyboard_patterns:
            if pattern in password_lower or pattern[::-1] in password_lower:
                errors.append("Password contains keyboard patterns (e.g., qwerty, asdf)")
                break
        
        return errors
    
    def _check_dictionary_words(self, password: str) -> List[str]:
        """Check for dictionary words."""
        errors = []
        password_lower = password.lower()
        
        # Simple dictionary check (in production, use a proper dictionary)
        common_words = [
            "password", "admin", "user", "login", "welcome", "hello",
            "computer", "internet", "security", "system", "database"
        ]
        
        for word in common_words:
            if word in password_lower:
                errors.append("Password contains common dictionary words")
                break
        
        return errors
    
    def _check_common_passwords(self, password: str) -> List[str]:
        """Check against common password lists."""
        errors = []
        
        if password.lower() in self._common_passwords:
            errors.append("Password is too common and easily guessable")
        
        if password in self.policy.custom_blacklist:
            errors.append("Password is in the custom blacklist")
        
        return errors
    
    def _check_user_info(self, password: str, user_info: Dict[str, str]) -> List[str]:
        """Check if password contains user information."""
        errors = []
        password_lower = password.lower()
        
        for key, value in user_info.items():
            if value and len(value) >= 3:
                if value.lower() in password_lower:
                    errors.append(f"Password must not contain {key}")
                    break
        
        return errors
    
    def _check_password_reuse(self, password: str, password_history: List[str]) -> List[str]:
        """Check if password was recently used."""
        errors = []
        
        # Hash the new password for comparison
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check against recent passwords
        recent_hashes = password_history[:self.policy.prevent_reuse_count]
        
        if password_hash in recent_hashes:
            errors.append(f"Password was used recently. Cannot reuse last {self.policy.prevent_reuse_count} passwords")
        
        return errors
    
    def _calculate_complexity_score(self, password: str) -> int:
        """Calculate password complexity score."""
        score = 0
        
        # Base score from length
        score += min(len(password), 20)  # Cap at 20 for length
        
        # Character type bonuses
        if re.search(r'[a-z]', password):
            score += self.policy.bonus_mixed_case
        
        if re.search(r'[A-Z]', password):
            score += self.policy.bonus_mixed_case
        
        if re.search(r'\d', password):
            score += self.policy.bonus_numbers
        
        if re.search(f'[{re.escape(self.policy.special_chars)}]', password):
            score += self.policy.bonus_special_chars
        
        # Length bonus
        if len(password) >= self.policy.bonus_length_threshold:
            score += 2
        
        # Diversity bonus
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:  # 70% unique characters
            score += 2
        
        return score
    
    def _determine_strength(self, password: str, complexity_score: int) -> PasswordStrength:
        """Determine password strength based on various factors."""
        # Base strength from complexity score
        if complexity_score >= 20:
            base_strength = PasswordStrength.VERY_STRONG
        elif complexity_score >= 15:
            base_strength = PasswordStrength.STRONG
        elif complexity_score >= 10:
            base_strength = PasswordStrength.GOOD
        elif complexity_score >= 6:
            base_strength = PasswordStrength.FAIR
        elif complexity_score >= 3:
            base_strength = PasswordStrength.WEAK
        else:
            base_strength = PasswordStrength.VERY_WEAK
        
        # Adjust for common patterns
        password_lower = password.lower()
        
        # Penalize common patterns
        if (password_lower in self._common_passwords or
            any(pattern in password_lower for pattern in self._keyboard_patterns)):
            base_strength = PasswordStrength(max(0, base_strength.value - 2))
        
        return base_strength
    
    def _generate_suggestions(self, password: str, has_upper: bool, has_lower: bool, 
                           has_digit: bool, has_special: bool) -> List[str]:
        """Generate suggestions for password improvement."""
        suggestions = []
        
        if len(password) < 12:
            suggestions.append("Make your password longer (12+ characters recommended)")
        
        if not has_upper:
            suggestions.append("Add uppercase letters")
        
        if not has_lower:
            suggestions.append("Add lowercase letters")
        
        if not has_digit:
            suggestions.append("Add numbers")
        
        if not has_special:
            suggestions.append("Add special characters")
        
        suggestions.append("Avoid common words and patterns")
        suggestions.append("Use a passphrase with multiple words")
        
        return suggestions
    
    def _load_common_passwords(self) -> Set[str]:
        """Load common passwords list."""
        # In production, load from file
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890", "password1",
            "123456789", "12345678", "12345", "1234", "111111",
            "dragon", "sunshine", "princess", "azerty", "trustno1"
        }
        
        if self.policy.common_passwords_file:
            try:
                with open(self.policy.common_passwords_file, 'r') as f:
                    for line in f:
                        common_passwords.add(line.strip().lower())
            except FileNotFoundError:
                pass
        
        return common_passwords
    
    def _generate_keyboard_patterns(self) -> List[str]:
        """Generate keyboard patterns to check against."""
        patterns = [
            # QWERTY rows
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            # Number row
            "1234567890",
            # Common sequences
            "abcdefghijklmnopqrstuvwxyz",
            # Repeated patterns
            "aaa", "111", "abc", "123"
        ]
        
        # Add shorter patterns
        extended_patterns = []
        for pattern in patterns:
            for i in range(len(pattern) - 2):
                extended_patterns.append(pattern[i:i+3])
        
        return patterns + extended_patterns


class AccountLockoutManager:
    """
    Advanced account lockout management with progressive penalties.
    
    Provides brute force protection, suspicious activity detection,
    and flexible lockout policies.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "max_failed_attempts": 5,
            "lockout_duration": 1800,  # 30 minutes
            "progressive_lockout": True,
            "lockout_multiplier": 2,
            "max_lockout_duration": 86400,  # 24 hours
            "reset_attempts_after": 3600,  # 1 hour
            "track_ip_attempts": True,
            "max_ip_attempts": 20,
            "ip_lockout_duration": 3600,  # 1 hour
            "suspicious_activity_threshold": 10,
            "enable_captcha_after": 3
        }
        
        if config:
            default_config.update(config)
        
        self.config = default_config
        self._lockouts: Dict[str, AccountLockout] = {}
        self._login_attempts: List[LoginAttempt] = []
        self._ip_attempts: Dict[str, List[datetime]] = {}
    
    def record_login_attempt(self, 
                           user_id: str, 
                           ip_address: str, 
                           success: bool,
                           user_agent: str = "",
                           metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Record a login attempt and check for lockout conditions.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            success: Whether login was successful
            user_agent: Client user agent
            metadata: Additional metadata
            
        Returns:
            Dictionary with lockout status and recommendations
        """
        attempt = LoginAttempt(
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=success,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        self._login_attempts.append(attempt)
        
        # Clean old attempts
        self._cleanup_old_attempts()
        
        result = {
            "locked": False,
            "lockout_reason": None,
            "lockout_duration": None,
            "attempts_remaining": None,
            "require_captcha": False,
            "suspicious_activity": False
        }
        
        if success:
            # Successful login - reset counters
            self._reset_user_attempts(user_id)
            return result
        
        # Failed login - check for lockout conditions
        user_attempts = self._get_recent_failed_attempts(user_id)
        ip_attempts = self._get_recent_ip_attempts(ip_address)
        
        # Check if user should be locked
        if len(user_attempts) >= self.config["max_failed_attempts"]:
            lockout_duration = self._calculate_lockout_duration(user_id)
            self._lock_account(user_id, LockoutReason.FAILED_ATTEMPTS, lockout_duration, ip_address)
            
            result.update({
                "locked": True,
                "lockout_reason": "failed_attempts",
                "lockout_duration": lockout_duration
            })
        else:
            remaining = self.config["max_failed_attempts"] - len(user_attempts)
            result["attempts_remaining"] = remaining
            
            # Check if captcha should be required
            if len(user_attempts) >= self.config["enable_captcha_after"]:
                result["require_captcha"] = True
        
        # Check IP-based lockout
        if self.config["track_ip_attempts"] and len(ip_attempts) >= self.config["max_ip_attempts"]:
            result["suspicious_activity"] = True
        
        # Check for suspicious activity patterns
        if self._detect_suspicious_activity(user_id, ip_address):
            result["suspicious_activity"] = True
        
        return result
    
    def is_account_locked(self, user_id: str) -> bool:
        """Check if account is currently locked."""
        lockout = self._lockouts.get(user_id)
        return lockout is not None and lockout.is_locked
    
    def get_lockout_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get lockout information for user."""
        lockout = self._lockouts.get(user_id)
        
        if not lockout or not lockout.is_locked:
            return None
        
        return {
            "reason": lockout.reason.value,
            "locked_at": lockout.locked_at.isoformat(),
            "locked_until": lockout.locked_until.isoformat() if lockout.locked_until else None,
            "time_remaining": lockout.time_remaining.total_seconds() if lockout.time_remaining else None,
            "attempt_count": lockout.attempt_count
        }
    
    def unlock_account(self, user_id: str, reason: str = "manual") -> bool:
        """
        Manually unlock an account.
        
        Args:
            user_id: User identifier
            reason: Reason for unlocking
            
        Returns:
            True if account was unlocked
        """
        if user_id in self._lockouts:
            lockout = self._lockouts[user_id]
            lockout.locked_until = datetime.utcnow()
            lockout.metadata["unlocked_reason"] = reason
            lockout.metadata["unlocked_at"] = datetime.utcnow().isoformat()
            return True
        
        return False
    
    def lock_account(self, 
                    user_id: str, 
                    reason: LockoutReason, 
                    duration: Optional[int] = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Manually lock an account.
        
        Args:
            user_id: User identifier
            reason: Reason for locking
            duration: Lock duration in seconds (None for permanent)
            metadata: Additional metadata
            
        Returns:
            True if account was locked
        """
        return self._lock_account(user_id, reason, duration, metadata=metadata)
    
    def get_failed_attempts_count(self, user_id: str) -> int:
        """Get number of recent failed attempts for user."""
        return len(self._get_recent_failed_attempts(user_id))
    
    def _lock_account(self, 
                     user_id: str, 
                     reason: LockoutReason, 
                     duration: Optional[int] = None,
                     ip_address: str = "",
                     metadata: Dict[str, Any] = None) -> bool:
        """Lock an account with specified parameters."""
        locked_until = None
        if duration is not None:
            locked_until = datetime.utcnow() + timedelta(seconds=duration)
        
        lockout = AccountLockout(
            user_id=user_id,
            reason=reason,
            locked_at=datetime.utcnow(),
            locked_until=locked_until,
            attempt_count=len(self._get_recent_failed_attempts(user_id)),
            metadata=metadata or {}
        )
        
        if ip_address:
            lockout.ip_addresses.add(ip_address)
        
        self._lockouts[user_id] = lockout
        return True
    
    def _calculate_lockout_duration(self, user_id: str) -> int:
        """Calculate lockout duration with progressive penalties."""
        base_duration = self.config["lockout_duration"]
        
        if not self.config["progressive_lockout"]:
            return base_duration
        
        # Check previous lockouts
        previous_lockouts = 0
        for attempt in self._login_attempts:
            if (attempt.user_id == user_id and 
                not attempt.success and 
                attempt.timestamp > datetime.utcnow() - timedelta(days=1)):
                previous_lockouts += 1
        
        # Progressive penalty
        multiplier = self.config["lockout_multiplier"] ** (previous_lockouts // self.config["max_failed_attempts"])
        duration = min(base_duration * multiplier, self.config["max_lockout_duration"])
        
        return int(duration)
    
    def _get_recent_failed_attempts(self, user_id: str) -> List[LoginAttempt]:
        """Get recent failed login attempts for user."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.config["reset_attempts_after"])
        
        return [
            attempt for attempt in self._login_attempts
            if (attempt.user_id == user_id and 
                not attempt.success and 
                attempt.timestamp > cutoff_time)
        ]
    
    def _get_recent_ip_attempts(self, ip_address: str) -> List[LoginAttempt]:
        """Get recent login attempts from IP address."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.config["reset_attempts_after"])
        
        return [
            attempt for attempt in self._login_attempts
            if (attempt.ip_address == ip_address and 
                not attempt.success and 
                attempt.timestamp > cutoff_time)
        ]
    
    def _reset_user_attempts(self, user_id: str):
        """Reset failed attempt counters for user."""
        # Remove recent failed attempts
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.config["reset_attempts_after"])
        self._login_attempts = [
            attempt for attempt in self._login_attempts
            if not (attempt.user_id == user_id and 
                   not attempt.success and 
                   attempt.timestamp > cutoff_time)
        ]
        
        # Remove lockout if exists
        if user_id in self._lockouts:
            del self._lockouts[user_id]
    
    def _detect_suspicious_activity(self, user_id: str, ip_address: str) -> bool:
        """Detect suspicious activity patterns."""
        recent_time = datetime.utcnow() - timedelta(hours=1)
        
        # Check for rapid attempts from multiple IPs
        user_attempts = [
            attempt for attempt in self._login_attempts
            if (attempt.user_id == user_id and 
                attempt.timestamp > recent_time)
        ]
        
        unique_ips = set(attempt.ip_address for attempt in user_attempts)
        
        # Suspicious if attempts from many different IPs
        if len(unique_ips) > 5:
            return True
        
        # Check for distributed attacks
        ip_attempts = [
            attempt for attempt in self._login_attempts
            if (attempt.ip_address == ip_address and 
                attempt.timestamp > recent_time)
        ]
        
        unique_users = set(attempt.user_id for attempt in ip_attempts)
        
        # Suspicious if many different users from same IP
        if len(unique_users) > 10:
            return True
        
        return False
    
    def _cleanup_old_attempts(self):
        """Remove old login attempts to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        self._login_attempts = [
            attempt for attempt in self._login_attempts
            if attempt.timestamp > cutoff_time
        ]
        
        # Clean up expired lockouts
        expired_lockouts = []
        for user_id, lockout in self._lockouts.items():
            if not lockout.is_locked:
                expired_lockouts.append(user_id)
        
        for user_id in expired_lockouts:
            del self._lockouts[user_id]


# Global instances
default_password_validator = PasswordValidator()
default_lockout_manager = AccountLockoutManager()