"""
User-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .common_types import BaseEntity, Timestamps, Status
from .auth_types import UserRole, UserStatus, UserProfile


class UserActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    POST_CREATED = "post_created"
    POST_UPDATED = "post_updated"
    POST_DELETED = "post_deleted"
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    PROFILE_UPDATED = "profile_updated"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_CHANGED = "email_changed"


class NotificationType(str, Enum):
    POST_LIKED = "post_liked"
    POST_COMMENTED = "post_commented"
    COMMENT_REPLIED = "comment_replied"
    USER_FOLLOWED = "user_followed"
    MENTION = "mention"
    NEWSLETTER = "newsletter"
    SYSTEM_ALERT = "system_alert"
    SECURITY_ALERT = "security_alert"


class BadgeType(str, Enum):
    EARLY_ADOPTER = "early_adopter"
    PROLIFIC_WRITER = "prolific_writer"
    HELPFUL_COMMENTER = "helpful_commenter"
    COMMUNITY_LEADER = "community_leader"
    VERIFIED_AUTHOR = "verified_author"
    TOP_CONTRIBUTOR = "top_contributor"


@dataclass
class UserStats:
    """User statistics"""
    posts_count: int = 0
    comments_count: int = 0
    likes_received: int = 0
    views_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    reputation_score: int = 0


@dataclass
class UserDetails(BaseEntity, Timestamps):
    """Extended user with additional fields"""
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
    date_joined: datetime = None
    profile: Optional[UserProfile] = None
    stats: UserStats = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = UserStats()
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username


@dataclass
class UserActivity(BaseEntity, Timestamps):
    """User activity log"""
    user_id: int
    activity_type: UserActivityType
    description: str
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserSearchFilters:
    """User search filters"""
    role: Optional[List[UserRole]] = None
    status: Optional[List[UserStatus]] = None
    is_verified: Optional[bool] = None
    is_staff: Optional[bool] = None
    date_joined_after: Optional[datetime] = None
    date_joined_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None


@dataclass
class UserListItem:
    """User list item for admin interface"""
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    date_joined: datetime
    last_login: Optional[datetime] = None
    posts_count: int = 0
    comments_count: int = 0


@dataclass
class UserCreateRequest:
    """User creation request (admin)"""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.SUBSCRIBER
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    is_staff: bool = False
    send_welcome_email: bool = True


@dataclass
class UserUpdateRequest:
    """User update request"""
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_verified: Optional[bool] = None
    is_staff: Optional[bool] = None


@dataclass
class ProfileUpdateRequest:
    """Profile update request"""
    avatar: Optional[Any] = None  # File or string
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


@dataclass
class UserNotification(BaseEntity, Timestamps):
    """User notification"""
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool = False
    is_seen: bool = False
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationPreferences:
    """Notification preferences"""
    email_enabled: bool = True
    push_enabled: bool = True
    types: Dict[NotificationType, Dict[str, bool]] = None
    
    def __post_init__(self):
        if self.types is None:
            self.types = {}


@dataclass
class UserFollow(BaseEntity, Timestamps):
    """User follow relationship"""
    follower_id: int
    following_id: int
    follower: Optional[UserListItem] = None
    following: Optional[UserListItem] = None


@dataclass
class UserBlock(BaseEntity, Timestamps):
    """User block relationship"""
    blocker_id: int
    blocked_id: int
    reason: Optional[str] = None


@dataclass
class UserReport(BaseEntity, Timestamps):
    """User report"""
    reporter_id: int
    reported_id: int
    reason: str
    description: str
    status: str = "pending"  # pending, reviewed, resolved, dismissed
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None


@dataclass
class UserBadge(BaseEntity, Timestamps):
    """User badge"""
    user_id: int
    badge_type: BadgeType
    name: str
    description: str
    icon: str
    color: str
    earned_at: datetime


@dataclass
class UserAchievement(BaseEntity, Timestamps):
    """User achievement"""
    user_id: int
    achievement_type: str
    name: str
    description: str
    points: int
    unlocked_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserSubscription(BaseEntity, Timestamps):
    """User subscription"""
    user_id: int
    plan_name: str
    status: str = "active"  # active, inactive, cancelled, expired
    starts_at: datetime = None
    ends_at: Optional[datetime] = None
    auto_renew: bool = True
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class UserAnalyticsSummary:
    """User analytics summary"""
    user_id: int
    period: str  # day, week, month, year
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                "profile_views": 0,
                "posts_created": 0,
                "comments_made": 0,
                "likes_received": 0,
                "shares_received": 0,
                "followers_gained": 0,
                "engagement_rate": 0.0,
            }