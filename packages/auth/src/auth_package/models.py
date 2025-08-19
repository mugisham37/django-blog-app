"""
Authentication models for users, roles, and relationships.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class UserStatus(Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class AuthProvider(Enum):
    """Authentication providers."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"


@dataclass
class UserProfile:
    """User profile information."""
    first_name: str = ""
    last_name: str = ""
    display_name: str = ""
    bio: str = ""
    avatar_url: str = ""
    phone_number: str = ""
    timezone: str = "UTC"
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get full name from first and last name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "phone_number": self.phone_number,
            "timezone": self.timezone,
            "language": self.language,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary."""
        return cls(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            display_name=data.get("display_name", ""),
            bio=data.get("bio", ""),
            avatar_url=data.get("avatar_url", ""),
            phone_number=data.get("phone_number", ""),
            timezone=data.get("timezone", "UTC"),
            language=data.get("language", "en"),
            metadata=data.get("metadata", {})
        )


@dataclass
class UserSecurity:
    """User security settings and MFA configuration."""
    password_hash: str = ""
    password_changed_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    last_login_ip: str = ""
    
    # MFA settings
    mfa_enabled: bool = False
    totp_secret: str = ""
    backup_codes: List[str] = field(default_factory=list)
    trusted_devices: List[Dict[str, Any]] = field(default_factory=list)
    
    # Security preferences
    require_password_change: bool = False
    session_timeout: int = 3600  # seconds
    max_concurrent_sessions: int = 5
    
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock account for specified duration."""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_failed_login(self, max_attempts: int = 5, lockout_duration: int = 30):
        """Record failed login attempt and lock if necessary."""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            self.lock_account(lockout_duration)
    
    def record_successful_login(self, ip_address: str = ""):
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def add_trusted_device(self, device_info: Dict[str, Any]):
        """Add trusted device."""
        device_info["added_at"] = datetime.utcnow().isoformat()
        self.trusted_devices.append(device_info)
    
    def remove_trusted_device(self, device_id: str):
        """Remove trusted device."""
        self.trusted_devices = [
            device for device in self.trusted_devices
            if device.get("device_id") != device_id
        ]
    
    def is_trusted_device(self, device_id: str) -> bool:
        """Check if device is trusted."""
        return any(
            device.get("device_id") == device_id
            for device in self.trusted_devices
        )


@dataclass
class User:
    """
    User model with authentication and profile information.
    
    Represents a user account with security settings, profile data,
    and role assignments for the authentication system.
    """
    id: str
    username: str
    email: str
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    auth_provider: AuthProvider = AuthProvider.LOCAL
    external_id: str = ""
    
    profile: UserProfile = field(default_factory=UserProfile)
    security: UserSecurity = field(default_factory=UserSecurity)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_activity_at: Optional[datetime] = None
    
    # Role assignments
    roles: Set[str] = field(default_factory=set)
    
    # Email verification
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    
    # Terms and privacy
    terms_accepted_at: Optional[datetime] = None
    privacy_accepted_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if not self.profile.display_name:
            self.profile.display_name = self.username
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE and not self.security.is_locked()
    
    @property
    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self.email_verified
    
    @property
    def requires_mfa(self) -> bool:
        """Check if user has MFA enabled."""
        return self.security.mfa_enabled
    
    def add_role(self, role_name: str):
        """Add role to user."""
        self.roles.add(role_name)
        self.updated_at = datetime.utcnow()
    
    def remove_role(self, role_name: str):
        """Remove role from user."""
        self.roles.discard(role_name)
        self.updated_at = datetime.utcnow()
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        return role_name in self.roles
    
    def activate(self):
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate user account."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self):
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        
        if self.status == UserStatus.PENDING_VERIFICATION:
            self.activate()
        
        self.updated_at = datetime.utcnow()
    
    def accept_terms(self):
        """Record terms acceptance."""
        self.terms_accepted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def accept_privacy(self):
        """Record privacy policy acceptance."""
        self.privacy_accepted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()
    
    def to_dict(self, include_security: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary.
        
        Args:
            include_security: Whether to include security information
            
        Returns:
            User data as dictionary
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "status": self.status.value,
            "auth_provider": self.auth_provider.value,
            "external_id": self.external_id,
            "profile": self.profile.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "roles": list(self.roles),
            "email_verified": self.email_verified,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            "terms_accepted_at": self.terms_accepted_at.isoformat() if self.terms_accepted_at else None,
            "privacy_accepted_at": self.privacy_accepted_at.isoformat() if self.privacy_accepted_at else None,
        }
        
        if include_security:
            data["security"] = {
                "password_changed_at": self.security.password_changed_at.isoformat() if self.security.password_changed_at else None,
                "failed_login_attempts": self.security.failed_login_attempts,
                "locked_until": self.security.locked_until.isoformat() if self.security.locked_until else None,
                "last_login_at": self.security.last_login_at.isoformat() if self.security.last_login_at else None,
                "last_login_ip": self.security.last_login_ip,
                "mfa_enabled": self.security.mfa_enabled,
                "require_password_change": self.security.require_password_change,
                "session_timeout": self.security.session_timeout,
                "max_concurrent_sessions": self.security.max_concurrent_sessions,
                "trusted_devices_count": len(self.security.trusted_devices)
            }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary."""
        user = cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            status=UserStatus(data.get("status", UserStatus.PENDING_VERIFICATION.value)),
            auth_provider=AuthProvider(data.get("auth_provider", AuthProvider.LOCAL.value)),
            external_id=data.get("external_id", ""),
            profile=UserProfile.from_dict(data.get("profile", {})),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            roles=set(data.get("roles", [])),
            email_verified=data.get("email_verified", False)
        )
        
        if data.get("last_activity_at"):
            user.last_activity_at = datetime.fromisoformat(data["last_activity_at"])
        
        if data.get("email_verified_at"):
            user.email_verified_at = datetime.fromisoformat(data["email_verified_at"])
        
        if data.get("terms_accepted_at"):
            user.terms_accepted_at = datetime.fromisoformat(data["terms_accepted_at"])
        
        if data.get("privacy_accepted_at"):
            user.privacy_accepted_at = datetime.fromisoformat(data["privacy_accepted_at"])
        
        return user


@dataclass
class UserRole:
    """
    User-Role assignment with additional metadata.
    
    Represents the relationship between a user and a role,
    including assignment context and expiration.
    """
    user_id: str
    role_name: str
    assigned_by: str = ""
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Check if role assignment has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_valid(self) -> bool:
        """Check if role assignment is valid."""
        return self.is_active and not self.is_expired
    
    def expire(self):
        """Mark role assignment as expired."""
        self.expires_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate role assignment."""
        self.is_active = False
    
    def extend_expiration(self, days: int):
        """Extend role expiration by specified days."""
        if self.expires_at:
            self.expires_at += timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "role_name": self.role_name,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "context": self.context,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRole':
        """Create from dictionary."""
        user_role = cls(
            user_id=data["user_id"],
            role_name=data["role_name"],
            assigned_by=data.get("assigned_by", ""),
            assigned_at=datetime.fromisoformat(data["assigned_at"]),
            context=data.get("context", {}),
            is_active=data.get("is_active", True)
        )
        
        if data.get("expires_at"):
            user_role.expires_at = datetime.fromisoformat(data["expires_at"])
        
        return user_role


class UserRepository:
    """
    Repository for user management operations.
    
    Provides CRUD operations and queries for user entities.
    In production, this would interface with a database.
    """
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._user_roles: Dict[str, List[UserRole]] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
        self._username_index: Dict[str, str] = {}  # username -> user_id
    
    def create_user(self, user: User) -> User:
        """Create a new user."""
        if user.id in self._users:
            raise ValueError(f"User with ID {user.id} already exists")
        
        if user.email in self._email_index:
            raise ValueError(f"User with email {user.email} already exists")
        
        if user.username in self._username_index:
            raise ValueError(f"User with username {user.username} already exists")
        
        self._users[user.id] = user
        self._email_index[user.email] = user.id
        self._username_index[user.username] = user.id
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_id = self._email_index.get(email)
        return self._users.get(user_id) if user_id else None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self._username_index.get(username)
        return self._users.get(user_id) if user_id else None
    
    def update_user(self, user: User) -> User:
        """Update existing user."""
        if user.id not in self._users:
            raise ValueError(f"User with ID {user.id} not found")
        
        old_user = self._users[user.id]
        
        # Update indexes if email or username changed
        if old_user.email != user.email:
            del self._email_index[old_user.email]
            self._email_index[user.email] = user.id
        
        if old_user.username != user.username:
            del self._username_index[old_user.username]
            self._username_index[user.username] = user.id
        
        user.updated_at = datetime.utcnow()
        self._users[user.id] = user
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        user = self._users.get(user_id)
        if not user:
            return False
        
        del self._users[user_id]
        del self._email_index[user.email]
        del self._username_index[user.username]
        
        # Clean up user roles
        if user_id in self._user_roles:
            del self._user_roles[user_id]
        
        return True
    
    def list_users(self, 
                   status: Optional[UserStatus] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[User]:
        """List users with optional filtering."""
        users = list(self._users.values())
        
        if status:
            users = [user for user in users if user.status == status]
        
        # Sort by created_at descending
        users.sort(key=lambda u: u.created_at, reverse=True)
        
        return users[offset:offset + limit]
    
    def assign_role_to_user(self, user_role: UserRole):
        """Assign role to user."""
        if user_role.user_id not in self._user_roles:
            self._user_roles[user_role.user_id] = []
        
        # Remove existing assignment if any
        self._user_roles[user_role.user_id] = [
            ur for ur in self._user_roles[user_role.user_id]
            if ur.role_name != user_role.role_name
        ]
        
        self._user_roles[user_role.user_id].append(user_role)
        
        # Update user roles set
        user = self.get_user_by_id(user_role.user_id)
        if user:
            user.add_role(user_role.role_name)
            self.update_user(user)
    
    def remove_role_from_user(self, user_id: str, role_name: str):
        """Remove role from user."""
        if user_id in self._user_roles:
            self._user_roles[user_id] = [
                ur for ur in self._user_roles[user_id]
                if ur.role_name != role_name
            ]
        
        # Update user roles set
        user = self.get_user_by_id(user_id)
        if user:
            user.remove_role(role_name)
            self.update_user(user)
    
    def get_user_roles(self, user_id: str) -> List[UserRole]:
        """Get all role assignments for user."""
        return self._user_roles.get(user_id, [])


# Global user repository instance
default_user_repository = UserRepository()