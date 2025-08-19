"""
WebSocket-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .user_types import UserListItem


class WebSocketStatus(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WebSocketEventType(str, Enum):
    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    RECONNECT = "reconnect"
    
    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    
    # Blog events
    POST_CREATED = "post_created"
    POST_UPDATED = "post_updated"
    POST_DELETED = "post_deleted"
    POST_PUBLISHED = "post_published"
    
    # Comment events
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    COMMENT_APPROVED = "comment_approved"
    
    # User events
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    USER_TYPING = "user_typing"
    USER_STOPPED_TYPING = "user_stopped_typing"
    
    # Notification events
    NOTIFICATION_CREATED = "notification_created"
    NOTIFICATION_READ = "notification_read"
    NOTIFICATION_DELETED = "notification_deleted"
    
    # System events
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"
    SYSTEM_ALERT = "system_alert"
    
    # Analytics events
    PAGE_VIEW = "page_view"
    USER_ACTIVITY = "user_activity"
    
    # Newsletter events
    NEWSLETTER_SENT = "newsletter_sent"
    NEWSLETTER_OPENED = "newsletter_opened"
    
    # Custom events
    CUSTOM_EVENT = "custom_event"


@dataclass
class WebSocketMessage:
    """WebSocket message"""
    id: str
    type: WebSocketEventType
    data: Any
    timestamp: datetime
    user_id: Optional[int] = None
    room: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSocketAuthMessage:
    """WebSocket authentication message"""
    token: str
    user_id: int
    rooms: Optional[List[str]] = None


@dataclass
class WebSocketErrorMessage:
    """WebSocket error message"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class WebSocketRoom:
    """WebSocket room"""
    name: str
    type: str = "public"  # public, private, protected
    participants: int = 0
    max_participants: Optional[int] = None
    created_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSocketConnection:
    """WebSocket connection info"""
    id: str
    user_id: Optional[int] = None
    user: Optional[UserListItem] = None
    ip_address: str = ""
    user_agent: str = ""
    connected_at: datetime = None
    last_activity: datetime = None
    rooms: List[str] = None
    status: WebSocketStatus = WebSocketStatus.DISCONNECTED
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []


@dataclass
class PostWebSocketEvent:
    """Post-related WebSocket event"""
    post_id: int
    title: str
    slug: str
    author: UserListItem
    action: str  # created, updated, deleted, published
    timestamp: datetime


@dataclass
class CommentWebSocketEvent:
    """Comment-related WebSocket event"""
    comment_id: int
    post_id: int
    content: str
    author: UserListItem
    action: str  # created, updated, deleted, approved
    timestamp: datetime


@dataclass
class UserActivityWebSocketEvent:
    """User activity WebSocket event"""
    user: UserListItem
    activity_type: str  # online, offline, typing, stopped_typing
    room: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationWebSocketEvent:
    """Notification WebSocket event"""
    notification_id: int
    user_id: int
    type: str
    title: str
    message: str
    action_url: Optional[str] = None
    action: str = "created"  # created, read, deleted
    timestamp: datetime = None


@dataclass
class SystemAlertWebSocketEvent:
    """System alert WebSocket event"""
    alert_id: str
    type: str = "info"  # maintenance, update, security, info
    title: str = ""
    message: str = ""
    severity: str = "low"  # low, medium, high, critical
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    affected_services: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.affected_services is None:
            self.affected_services = []


@dataclass
class WebSocketClientConfig:
    """WebSocket client configuration"""
    url: str
    protocols: Optional[List[str]] = None
    reconnect: bool = True
    reconnect_interval: int = 5000
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30000
    auth_token: Optional[str] = None
    rooms: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.protocols is None:
            self.protocols = []
        if self.rooms is None:
            self.rooms = []


@dataclass
class WebSocketServerConfig:
    """WebSocket server configuration"""
    port: int = 8000
    path: str = "/ws/"
    cors: Dict[str, Any] = None
    auth: Dict[str, Any] = None
    rate_limit: Dict[str, Any] = None
    rooms: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cors is None:
            self.cors = {
                "origin": "*",
                "credentials": True,
            }
        if self.auth is None:
            self.auth = {
                "required": True,
                "token_header": "Authorization",
            }
        if self.rate_limit is None:
            self.rate_limit = {
                "enabled": True,
                "max_connections_per_ip": 10,
                "max_messages_per_minute": 60,
            }
        if self.rooms is None:
            self.rooms = {
                "max_rooms_per_connection": 10,
                "auto_join_public_rooms": False,
            }


@dataclass
class WebSocketMetrics:
    """WebSocket metrics"""
    total_connections: int = 0
    active_connections: int = 0
    total_messages: int = 0
    messages_per_second: float = 0.0
    rooms_count: int = 0
    average_connection_duration: float = 0.0
    error_rate: float = 0.0
    reconnection_rate: float = 0.0