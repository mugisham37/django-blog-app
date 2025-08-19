"""
Analytics-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .common_types import BaseEntity, Timestamps
from .user_types import UserListItem


class AnalyticsEventType(str, Enum):
    PAGE_VIEW = "page_view"
    POST_VIEW = "post_view"
    POST_LIKE = "post_like"
    POST_SHARE = "post_share"
    COMMENT_CREATE = "comment_create"
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"
    SEARCH_QUERY = "search_query"
    NEWSLETTER_SUBSCRIBE = "newsletter_subscribe"
    DOWNLOAD = "download"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    ERROR = "error"


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TV = "tv"
    WEARABLE = "wearable"
    UNKNOWN = "unknown"


class BrowserType(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    OPERA = "opera"
    IE = "ie"
    OTHER = "other"


class OSType(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    OTHER = "other"


class TrafficSource(str, Enum):
    DIRECT = "direct"
    SEARCH = "search"
    SOCIAL = "social"
    EMAIL = "email"
    REFERRAL = "referral"
    PAID = "paid"
    OTHER = "other"


@dataclass
class PageView(BaseEntity, Timestamps):
    """Page view analytics"""
    url: str
    title: Optional[str] = None
    user_id: Optional[int] = None
    user: Optional[UserListItem] = None
    session_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    browser: BrowserType = BrowserType.OTHER
    os: OSType = OSType.OTHER
    screen_resolution: Optional[str] = None
    viewport_size: Optional[str] = None
    language: str = "en"
    country: Optional[str] = None
    city: Optional[str] = None
    duration: Optional[int] = None
    bounce: bool = False


@dataclass
class SearchQuery(BaseEntity, Timestamps):
    """Search query analytics"""
    query: str
    user_id: Optional[int] = None
    user: Optional[UserListItem] = None
    session_id: str = ""
    ip_address: str = ""
    results_count: int = 0
    clicked_result: Optional[int] = None
    no_results: bool = False
    filters_used: Dict[str, Any] = None
    sort_order: Optional[str] = None
    
    def __post_init__(self):
        if self.filters_used is None:
            self.filters_used = {}


@dataclass
class UserActivity(BaseEntity, Timestamps):
    """User activity analytics"""
    user_id: int
    user: Optional[UserListItem] = None
    event_type: AnalyticsEventType = AnalyticsEventType.PAGE_VIEW
    event_data: Dict[str, Any] = None
    session_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    page_url: str = ""
    referrer: Optional[str] = None
    
    def __post_init__(self):
        if self.event_data is None:
            self.event_data = {}


@dataclass
class ConversionEvent(BaseEntity, Timestamps):
    """Conversion event"""
    event_name: str
    user_id: Optional[int] = None
    user: Optional[UserListItem] = None
    session_id: str = ""
    value: Optional[float] = None
    currency: Optional[str] = None
    properties: Dict[str, Any] = None
    funnel_step: Optional[int] = None
    attribution_source: Optional[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class DashboardMetrics:
    """Analytics dashboard metrics"""
    period: str  # today, yesterday, week, month, quarter, year
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, Any] = None
    comparison: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                "total_visitors": 0,
                "unique_visitors": 0,
                "page_views": 0,
                "bounce_rate": 0.0,
                "avg_session_duration": 0,
                "new_users": 0,
                "returning_users": 0,
                "conversion_rate": 0.0,
            }


@dataclass
class TrafficAnalytics:
    """Traffic analytics"""
    period: str
    start_date: datetime
    end_date: datetime
    sources: List[Dict[str, Any]] = None
    referrers: List[Dict[str, Any]] = None
    campaigns: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.referrers is None:
            self.referrers = []
        if self.campaigns is None:
            self.campaigns = []


@dataclass
class ContentAnalytics:
    """Content analytics"""
    period: str
    start_date: datetime
    end_date: datetime
    popular_pages: List[Dict[str, Any]] = None
    popular_posts: List[Dict[str, Any]] = None
    search_terms: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.popular_pages is None:
            self.popular_pages = []
        if self.popular_posts is None:
            self.popular_posts = []
        if self.search_terms is None:
            self.search_terms = []


@dataclass
class RealTimeAnalytics:
    """Real-time analytics"""
    active_users: int = 0
    active_sessions: int = 0
    current_page_views: int = 0
    top_pages: List[Dict[str, Any]] = None
    traffic_sources: List[Dict[str, Any]] = None
    locations: List[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.top_pages is None:
            self.top_pages = []
        if self.traffic_sources is None:
            self.traffic_sources = []
        if self.locations is None:
            self.locations = []
        if self.events is None:
            self.events = []


@dataclass
class AnalyticsReport:
    """Analytics report"""
    id: int
    name: str
    description: Optional[str] = None
    report_type: str = "traffic"  # traffic, content, user_behavior, conversion, custom
    filters: Dict[str, Any] = None
    metrics: List[str] = None
    dimensions: List[str] = None
    date_range: Dict[str, str] = None
    schedule: Optional[Dict[str, Any]] = None
    created_by: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.metrics is None:
            self.metrics = []
        if self.dimensions is None:
            self.dimensions = []
        if self.date_range is None:
            self.date_range = {}


@dataclass
class AnalyticsGoal:
    """Analytics goal"""
    id: int
    name: str
    description: Optional[str] = None
    goal_type: str = "page_views"  # page_views, conversions, revenue, engagement
    target_value: float = 0
    current_value: float = 0
    progress_percentage: float = 0
    period: str = "monthly"  # daily, weekly, monthly, quarterly, yearly
    start_date: datetime = None
    end_date: datetime = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None