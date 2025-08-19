"""
Shared Python type definitions for enterprise fullstack monolith
"""

from .auth_types import *
from .blog_types import *
from .user_types import *
from .api_types import *
from .common_types import *
from .analytics_types import *
from .newsletter_types import *
from .websocket_types import *
from .cache_types import *
from .database_types import *

__version__ = "1.0.0"
__all__ = [
    # Auth types
    "UserRole",
    "UserStatus",
    "Permission",
    "AuthProvider",
    "MFAMethod",
    "SecurityEventType",
    
    # Blog types
    "PostStatus",
    "ContentFormat",
    "Visibility",
    
    # User types
    "UserActivityType",
    "NotificationType",
    "BadgeType",
    
    # API types
    "HTTPStatus",
    "APIResponse",
    "PaginatedResponse",
    "APIError",
    
    # Common types
    "Status",
    "Priority",
    "SortOrder",
    "FilterOperator",
    "Environment",
    "LogLevel",
    
    # Analytics types
    "AnalyticsEventType",
    "DeviceType",
    "BrowserType",
    "OSType",
    "TrafficSource",
    
    # Newsletter types
    "SubscriptionStatus",
    "CampaignStatus",
    "CampaignType",
    "TemplateType",
    
    # WebSocket types
    "WebSocketStatus",
    "WebSocketEventType",
    
    # Cache types
    "CacheProvider",
    "CacheStrategy",
    "CacheEvictionPolicy",
    
    # Database types
    "DatabaseProvider",
    "IsolationLevel",
    "DatabaseEventType",
]