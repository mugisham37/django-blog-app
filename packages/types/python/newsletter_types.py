"""
Newsletter-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .common_types import BaseEntity, Timestamps
from .user_types import UserListItem


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignType(str, Enum):
    NEWSLETTER = "newsletter"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    WELCOME = "welcome"
    ANNOUNCEMENT = "announcement"
    DIGEST = "digest"


class TemplateType(str, Enum):
    NEWSLETTER = "newsletter"
    WELCOME = "welcome"
    CONFIRMATION = "confirmation"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    CUSTOM = "custom"


@dataclass
class SubscriberPreferences:
    """Subscriber preferences"""
    frequency: str = "weekly"  # daily, weekly, monthly, never
    categories: List[str] = None
    format: str = "html"  # html, text
    language: str = "en"
    timezone: str = "UTC"
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []


@dataclass
class NewsletterSubscriber(BaseEntity, Timestamps):
    """Newsletter subscriber"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_id: Optional[int] = None
    user: Optional[UserListItem] = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    subscribed_at: datetime = None
    unsubscribed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    bounce_count: int = 0
    complaint_count: int = 0
    tags: List[str] = None
    preferences: SubscriberPreferences = None
    source: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.preferences is None:
            self.preferences = SubscriberPreferences()


@dataclass
class SubscriptionRequest:
    """Newsletter subscription request"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[SubscriberPreferences] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    double_opt_in: bool = True


@dataclass
class UnsubscriptionRequest:
    """Newsletter unsubscription request"""
    email: Optional[str] = None
    token: Optional[str] = None
    reason: Optional[str] = None
    feedback: Optional[str] = None


@dataclass
class TemplateVariable:
    """Template variable"""
    name: str
    type: str = "text"  # text, number, date, boolean, url, email
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False


@dataclass
class EmailTemplate(BaseEntity, Timestamps):
    """Email template"""
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_type: TemplateType = TemplateType.NEWSLETTER
    is_active: bool = True
    variables: List[TemplateVariable] = None
    preview_text: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.tags is None:
            self.tags = []


@dataclass
class SegmentCondition:
    """Segment condition"""
    field: str
    operator: str  # equals, not_equals, contains, not_contains, starts_with, ends_with, in, not_in
    value: Any


@dataclass
class CampaignSegment:
    """Campaign segment"""
    name: str
    conditions: List[SegmentCondition]
    subscriber_count: int = 0


@dataclass
class TrackingSettings:
    """Tracking settings"""
    open_tracking: bool = True
    click_tracking: bool = True
    unsubscribe_tracking: bool = True
    google_analytics: bool = False
    custom_domain: Optional[str] = None


@dataclass
class NewsletterCampaign(BaseEntity, Timestamps):
    """Newsletter campaign"""
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_id: Optional[int] = None
    template: Optional[EmailTemplate] = None
    campaign_type: CampaignType = CampaignType.NEWSLETTER
    status: CampaignStatus = CampaignStatus.DRAFT
    from_name: str = ""
    from_email: str = ""
    reply_to: Optional[str] = None
    preview_text: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    recipient_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    bounced_count: int = 0
    complained_count: int = 0
    unsubscribed_count: int = 0
    tags: List[str] = None
    segments: List[CampaignSegment] = None
    tracking_settings: TrackingSettings = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.segments is None:
            self.segments = []
        if self.tracking_settings is None:
            self.tracking_settings = TrackingSettings()


@dataclass
class CampaignCreateRequest:
    """Campaign creation request"""
    name: str
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_id: Optional[int] = None
    campaign_type: CampaignType = CampaignType.NEWSLETTER
    from_name: str = ""
    from_email: str = ""
    reply_to: Optional[str] = None
    preview_text: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    segments: Optional[List[CampaignSegment]] = None
    tracking_settings: Optional[TrackingSettings] = None


@dataclass
class EmailEvent(BaseEntity, Timestamps):
    """Email event"""
    campaign_id: Optional[int] = None
    subscriber_id: int = 0
    subscriber: Optional[NewsletterSubscriber] = None
    event_type: str = ""  # sent, delivered, opened, clicked, bounced, complained, unsubscribed
    email_address: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    url: Optional[str] = None  # For click events
    bounce_reason: Optional[str] = None  # For bounce events
    complaint_reason: Optional[str] = None  # For complaint events
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NewsletterList(BaseEntity, Timestamps):
    """Newsletter list"""
    name: str
    description: Optional[str] = None
    is_active: bool = True
    subscriber_count: int = 0
    default_from_name: str = ""
    default_from_email: str = ""
    default_reply_to: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class WorkflowTrigger:
    """Workflow trigger"""
    type: str  # subscription, tag_added, date, behavior, api
    conditions: Dict[str, Any] = None
    delay: Optional[int] = None  # in minutes
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}


@dataclass
class WorkflowStep:
    """Workflow step"""
    id: str
    type: str  # email, delay, condition, tag, webhook
    config: Dict[str, Any] = None
    next_step_id: Optional[str] = None
    condition_steps: Optional[List[Dict[str, str]]] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class AutomationWorkflow(BaseEntity, Timestamps):
    """Automation workflow"""
    name: str
    description: Optional[str] = None
    trigger: WorkflowTrigger = None
    steps: List[WorkflowStep] = None
    is_active: bool = True
    subscriber_count: int = 0
    completion_rate: float = 0.0
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []