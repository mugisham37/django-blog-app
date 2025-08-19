"""
Authentication and authorization Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .common_types import BaseEntity, Timestamps


class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    EDITOR = "editor"
    AUTHOR = "author"
    SUBSCRIBER = "subscriber"
    GUEST = "guest"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    BANNED = "banned"


class Permission(str, Enum):
    # User management
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_LIST = "user.list"

    # Blog management
    POST_CREATE = "post.create"
    POST_READ = "post.read"
    POST_UPDATE = "post.update"
    POST_DELETE = "post.delete"
    POST_PUBLISH = "post.publish"
    POST_LIST = "post.list"

    # Comment management
    COMMENT_CREATE = "comment.create"
    COMMENT_READ = "comment.read"
    COMMENT_UPDATE = "comment.update"
    COMMENT_DELETE = "comment.delete"
    COMMENT_MODERATE = "comment.moderate"

    # Analytics
    ANALYTICS_READ = "analytics.read"
    ANALYTICS_EXPORT = "analytics.export"

    # Newsletter
    NEWSLETTER_CREATE = "newsletter.create"
    NEWSLETTER_SEND = "newsletter.send"
    NEWSLETTER_MANAGE = "newsletter.manage"

    # System administration
    SYSTEM_CONFIG = "system.config"
    SYSTEM_MONITOR = "system.monitor"
    SYSTEM_BACKUP = "system.backup"


class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    GITHUB = "github"
    LINKEDIN = "linkedin"


class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_CHANGED = "email_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class EmailNotificationSettings:
    """Email notification preferences"""
    new_posts: bool = True
    new_comments: bool = True
    newsletter: bool = True
    security_alerts: bool = True
    marketing: bool = False


@dataclass
class PushNotificationSettings:
    """Push notification preferences"""
    enabled: bool = True
    new_posts: bool = True
    new_comments: bool = True
    mentions: bool = True


@dataclass
class UserPreferences:
    """User preferences"""
    language: str = "en"
    timezone: str = "UTC"
    theme: str = "light"  # light, dark, auto
    email_notifications: EmailNotificationSettings = None
    push_notifications: PushNotificationSettings = None
    
    def __post_init__(self):
        if self.email_notifications is None:
            self.email_notifications = EmailNotificationSettings()
        if self.push_notifications is None:
            self.push_notifications = PushNotificationSettings()


@dataclass
class PrivacySettings:
    """Privacy settings"""
    profile_visibility: str = "public"  # public, private, friends
    email_visibility: bool = False
    activity_visibility: bool = True
    search_indexing: bool = True


@dataclass
class UserProfile(BaseEntity, Timestamps):
    """User profile"""
    user_id: int
    avatar: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    social_links: Dict[str, str] = None
    preferences: UserPreferences = None
    privacy_settings: PrivacySettings = None
    
    def __post_init__(self):
        if self.social_links is None:
            self.social_links = {}
        if self.preferences is None:
            self.preferences = UserPreferences()
        if self.privacy_settings is None:
            self.privacy_settings = PrivacySettings()


@dataclass
class User(BaseEntity, Timestamps):
    """User entity"""
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.SUBSCRIBER
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    profile: Optional[UserProfile] = None
    permissions: List[Permission] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def is_active_user(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE


@dataclass
class LoginRequest:
    """Login request data"""
    email: str
    password: str
    remember_me: bool = False
    mfa_code: Optional[str] = None


@dataclass
class RegisterRequest:
    """Registration request data"""
    username: str
    email: str
    password: str
    password_confirm: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    terms_accepted: bool = False
    newsletter_opt_in: bool = False


@dataclass
class PasswordResetRequest:
    """Password reset request"""
    email: str


@dataclass
class PasswordResetConfirm:
    """Password reset confirmation"""
    token: str
    password: str
    password_confirm: str


@dataclass
class ChangePasswordRequest:
    """Change password request"""
    current_password: str
    new_password: str
    new_password_confirm: str


@dataclass
class JWTPayload:
    """JWT token payload"""
    user_id: int
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    iat: int
    exp: int
    jti: str


@dataclass
class OAuth2AuthRequest:
    """OAuth2 authorization request"""
    provider: AuthProvider
    redirect_uri: str
    state: Optional[str] = None
    scope: Optional[List[str]] = None


@dataclass
class OAuth2CallbackData:
    """OAuth2 callback data"""
    provider: AuthProvider
    code: str
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


@dataclass
class MFASetupRequest:
    """MFA setup request"""
    method: MFAMethod
    phone_number: Optional[str] = None  # For SMS
    email: Optional[str] = None  # For email


@dataclass
class MFASetupResponse:
    """MFA setup response"""
    method: MFAMethod
    secret: Optional[str] = None  # For TOTP
    qr_code: Optional[str] = None  # For TOTP
    backup_codes: Optional[List[str]] = None  # For backup codes


@dataclass
class MFAVerificationRequest:
    """MFA verification request"""
    method: MFAMethod
    code: str


@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    user_id: int
    ip_address: str
    user_agent: str
    location: Optional[str] = None
    device_type: str = "desktop"  # desktop, mobile, tablet
    is_current: bool = False
    created_at: datetime = None
    last_activity: datetime = None
    expires_at: datetime = None


@dataclass
class SecurityEvent(BaseEntity, Timestamps):
    """Security event"""
    user_id: int
    event_type: SecurityEventType
    ip_address: str
    user_agent: str
    location: Optional[str] = None
    details: Dict[str, Any] = None
    risk_score: int = 0
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class Role(BaseEntity, Timestamps):
    """Role definition"""
    name: str
    description: str
    permissions: List[Permission]
    is_system: bool = False


@dataclass
class PermissionCheckRequest:
    """Permission check request"""
    user_id: int
    permission: Permission
    resource_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class PermissionCheckResponse:
    """Permission check response"""
    allowed: bool
    reason: Optional[str] = None


@dataclass
class AccountVerification:
    """Account verification"""
    token: str
    email: str
    expires_at: datetime


@dataclass
class PasswordPolicy:
    """Password policy configuration"""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_symbols: bool = True
    prevent_common: bool = True
    prevent_personal: bool = True
    history_count: int = 5
    max_age_days: int = 90