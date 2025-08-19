/**
 * WebSocket-related type definitions
 */

import { UserListItem } from "./user";

// WebSocket connection status
export enum WebSocketStatus {
  CONNECTING = "connecting",
  CONNECTED = "connected",
  DISCONNECTING = "disconnecting",
  DISCONNECTED = "disconnected",
  ERROR = "error",
}

// WebSocket event types
export enum WebSocketEventType {
  // Connection events
  CONNECT = "connect",
  DISCONNECT = "disconnect",
  ERROR = "error",
  RECONNECT = "reconnect",

  // Authentication events
  AUTH_SUCCESS = "auth_success",
  AUTH_FAILED = "auth_failed",

  // Blog events
  POST_CREATED = "post_created",
  POST_UPDATED = "post_updated",
  POST_DELETED = "post_deleted",
  POST_PUBLISHED = "post_published",

  // Comment events
  COMMENT_CREATED = "comment_created",
  COMMENT_UPDATED = "comment_updated",
  COMMENT_DELETED = "comment_deleted",
  COMMENT_APPROVED = "comment_approved",

  // User events
  USER_ONLINE = "user_online",
  USER_OFFLINE = "user_offline",
  USER_TYPING = "user_typing",
  USER_STOPPED_TYPING = "user_stopped_typing",

  // Notification events
  NOTIFICATION_CREATED = "notification_created",
  NOTIFICATION_READ = "notification_read",
  NOTIFICATION_DELETED = "notification_deleted",

  // System events
  SYSTEM_MAINTENANCE = "system_maintenance",
  SYSTEM_UPDATE = "system_update",
  SYSTEM_ALERT = "system_alert",

  // Analytics events
  PAGE_VIEW = "page_view",
  USER_ACTIVITY = "user_activity",

  // Newsletter events
  NEWSLETTER_SENT = "newsletter_sent",
  NEWSLETTER_OPENED = "newsletter_opened",

  // Custom events
  CUSTOM_EVENT = "custom_event",
}

// WebSocket message interface
export interface WebSocketMessage<T = unknown> {
  readonly id: string;
  readonly type: WebSocketEventType;
  readonly data: T;
  readonly timestamp: string;
  readonly user_id?: number;
  readonly room?: string;
  readonly metadata?: Record<string, unknown>;
}

// WebSocket authentication message
export interface WebSocketAuthMessage {
  readonly token: string;
  readonly user_id: number;
  readonly rooms?: string[];
}

// WebSocket error message
export interface WebSocketErrorMessage {
  readonly code: string;
  readonly message: string;
  readonly details?: Record<string, unknown>;
}

// WebSocket room interface
export interface WebSocketRoom {
  readonly name: string;
  readonly type: "public" | "private" | "protected";
  readonly participants: number;
  readonly max_participants?: number;
  readonly created_at: string;
  readonly metadata?: Record<string, unknown>;
}

// WebSocket connection info
export interface WebSocketConnection {
  readonly id: string;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly connected_at: string;
  readonly last_activity: string;
  readonly rooms: string[];
  readonly status: WebSocketStatus;
}

// Post-related WebSocket events
export interface PostWebSocketEvent {
  readonly post_id: number;
  readonly title: string;
  readonly slug: string;
  readonly author: UserListItem;
  readonly action: "created" | "updated" | "deleted" | "published";
  readonly timestamp: string;
}

// Comment-related WebSocket events
export interface CommentWebSocketEvent {
  readonly comment_id: number;
  readonly post_id: number;
  readonly content: string;
  readonly author: UserListItem;
  readonly action: "created" | "updated" | "deleted" | "approved";
  readonly timestamp: string;
}

// User activity WebSocket event
export interface UserActivityWebSocketEvent {
  readonly user: UserListItem;
  readonly activity_type: "online" | "offline" | "typing" | "stopped_typing";
  readonly room?: string;
  readonly timestamp: string;
  readonly metadata?: Record<string, unknown>;
}

// Notification WebSocket event
export interface NotificationWebSocketEvent {
  readonly notification_id: number;
  readonly user_id: number;
  readonly type: string;
  readonly title: string;
  readonly message: string;
  readonly action_url?: string;
  readonly action: "created" | "read" | "deleted";
  readonly timestamp: string;
}

// System alert WebSocket event
export interface SystemAlertWebSocketEvent {
  readonly alert_id: string;
  readonly type: "maintenance" | "update" | "security" | "info";
  readonly title: string;
  readonly message: string;
  readonly severity: "low" | "medium" | "high" | "critical";
  readonly start_time?: string;
  readonly end_time?: string;
  readonly affected_services?: string[];
}

// Analytics WebSocket event
export interface AnalyticsWebSocketEvent {
  readonly event_type: "page_view" | "user_activity" | "conversion";
  readonly data: Record<string, unknown>;
  readonly timestamp: string;
}

// Newsletter WebSocket event
export interface NewsletterWebSocketEvent {
  readonly campaign_id: number;
  readonly campaign_name: string;
  readonly event_type: "sent" | "opened" | "clicked" | "bounced";
  readonly subscriber_count?: number;
  readonly timestamp: string;
}

// WebSocket client configuration
export interface WebSocketClientConfig {
  readonly url: string;
  readonly protocols?: string[];
  readonly reconnect: boolean;
  readonly reconnect_interval: number;
  readonly max_reconnect_attempts: number;
  readonly heartbeat_interval: number;
  readonly auth_token?: string;
  readonly rooms?: string[];
}

// WebSocket server configuration
export interface WebSocketServerConfig {
  readonly port: number;
  readonly path: string;
  readonly cors: {
    readonly origin: string | string[];
    readonly credentials: boolean;
  };
  readonly auth: {
    readonly required: boolean;
    readonly token_header: string;
  };
  readonly rate_limit: {
    readonly enabled: boolean;
    readonly max_connections_per_ip: number;
    readonly max_messages_per_minute: number;
  };
  readonly rooms: {
    readonly max_rooms_per_connection: number;
    readonly auto_join_public_rooms: boolean;
  };
}

// WebSocket middleware interface
export interface WebSocketMiddleware {
  readonly name: string;
  readonly handler: (
    connection: WebSocketConnection,
    message: WebSocketMessage,
    next: () => void
  ) => void | Promise<void>;
}

// WebSocket event handler interface
export interface WebSocketEventHandler<T = unknown> {
  readonly event_type: WebSocketEventType;
  readonly handler: (
    connection: WebSocketConnection,
    data: T
  ) => void | Promise<void>;
}

// WebSocket room manager interface
export interface WebSocketRoomManager {
  readonly join: (connection_id: string, room: string) => Promise<boolean>;
  readonly leave: (connection_id: string, room: string) => Promise<boolean>;
  readonly broadcast: (
    room: string,
    message: WebSocketMessage
  ) => Promise<void>;
  readonly get_room_participants: (
    room: string
  ) => Promise<WebSocketConnection[]>;
  readonly get_user_rooms: (user_id: number) => Promise<string[]>;
}

// WebSocket metrics
export interface WebSocketMetrics {
  readonly total_connections: number;
  readonly active_connections: number;
  readonly total_messages: number;
  readonly messages_per_second: number;
  readonly rooms_count: number;
  readonly average_connection_duration: number;
  readonly error_rate: number;
  readonly reconnection_rate: number;
}

// WebSocket connection pool
export interface WebSocketConnectionPool {
  readonly add_connection: (connection: WebSocketConnection) => void;
  readonly remove_connection: (connection_id: string) => void;
  readonly get_connection: (
    connection_id: string
  ) => WebSocketConnection | null;
  readonly get_user_connections: (user_id: number) => WebSocketConnection[];
  readonly get_room_connections: (room: string) => WebSocketConnection[];
  readonly broadcast_to_user: (
    user_id: number,
    message: WebSocketMessage
  ) => Promise<void>;
  readonly broadcast_to_room: (
    room: string,
    message: WebSocketMessage
  ) => Promise<void>;
  readonly get_metrics: () => WebSocketMetrics;
}

// WebSocket message queue
export interface WebSocketMessageQueue {
  readonly enqueue: (
    connection_id: string,
    message: WebSocketMessage
  ) => Promise<void>;
  readonly dequeue: (connection_id: string) => Promise<WebSocketMessage | null>;
  readonly get_queue_size: (connection_id: string) => Promise<number>;
  readonly clear_queue: (connection_id: string) => Promise<void>;
}

// WebSocket presence system
export interface WebSocketPresence {
  readonly set_online: (
    user_id: number,
    connection_id: string
  ) => Promise<void>;
  readonly set_offline: (
    user_id: number,
    connection_id: string
  ) => Promise<void>;
  readonly is_online: (user_id: number) => Promise<boolean>;
  readonly get_online_users: () => Promise<number[]>;
  readonly get_user_connections: (user_id: number) => Promise<string[]>;
}
