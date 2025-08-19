/**
 * User-related type definitions
 */

import { BaseEntity, Timestamps, Status } from "./common";
import { UserRole, UserStatus, UserProfile } from "./auth";

// Extended user interface with additional fields
export interface UserDetails extends BaseEntity, Timestamps {
  readonly username: string;
  readonly email: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly full_name: string;
  readonly role: UserRole;
  readonly status: UserStatus;
  readonly is_verified: boolean;
  readonly is_staff: boolean;
  readonly is_superuser: boolean;
  readonly last_login?: string;
  readonly date_joined: string;
  readonly profile: UserProfile;
  readonly stats: UserStats;
}

// User statistics
export interface UserStats {
  readonly posts_count: number;
  readonly comments_count: number;
  readonly likes_received: number;
  readonly views_count: number;
  readonly followers_count: number;
  readonly following_count: number;
  readonly reputation_score: number;
}

// User activity types
export enum UserActivityType {
  LOGIN = "login",
  LOGOUT = "logout",
  POST_CREATED = "post_created",
  POST_UPDATED = "post_updated",
  POST_DELETED = "post_deleted",
  COMMENT_CREATED = "comment_created",
  COMMENT_UPDATED = "comment_updated",
  COMMENT_DELETED = "comment_deleted",
  PROFILE_UPDATED = "profile_updated",
  PASSWORD_CHANGED = "password_changed",
  EMAIL_CHANGED = "email_changed",
}

// User activity log
export interface UserActivity extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly activity_type: UserActivityType;
  readonly description: string;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly metadata: Record<string, unknown>;
}

// User search filters
export interface UserSearchFilters {
  readonly role?: UserRole[];
  readonly status?: UserStatus[];
  readonly is_verified?: boolean;
  readonly is_staff?: boolean;
  readonly date_joined_after?: string;
  readonly date_joined_before?: string;
  readonly last_login_after?: string;
  readonly last_login_before?: string;
}

// User list item (for admin interface)
export interface UserListItem {
  readonly id: number;
  readonly username: string;
  readonly email: string;
  readonly full_name: string;
  readonly role: UserRole;
  readonly status: UserStatus;
  readonly is_verified: boolean;
  readonly date_joined: string;
  readonly last_login?: string;
  readonly posts_count: number;
  readonly comments_count: number;
}

// User creation request (admin)
export interface UserCreateRequest {
  readonly username: string;
  readonly email: string;
  readonly password: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly role: UserRole;
  readonly status: UserStatus;
  readonly is_verified?: boolean;
  readonly is_staff?: boolean;
  readonly send_welcome_email?: boolean;
}

// User update request
export interface UserUpdateRequest {
  readonly username?: string;
  readonly email?: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly role?: UserRole;
  readonly status?: UserStatus;
  readonly is_verified?: boolean;
  readonly is_staff?: boolean;
}

// Profile update request
export interface ProfileUpdateRequest {
  readonly avatar?: File | string;
  readonly bio?: string;
  readonly website?: string;
  readonly location?: string;
  readonly birth_date?: string;
  readonly phone_number?: string;
  readonly social_links?: Record<string, string>;
}

// User notification types
export enum NotificationType {
  POST_LIKED = "post_liked",
  POST_COMMENTED = "post_commented",
  COMMENT_REPLIED = "comment_replied",
  USER_FOLLOWED = "user_followed",
  MENTION = "mention",
  NEWSLETTER = "newsletter",
  SYSTEM_ALERT = "system_alert",
  SECURITY_ALERT = "security_alert",
}

// User notification
export interface UserNotification extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly type: NotificationType;
  readonly title: string;
  readonly message: string;
  readonly is_read: boolean;
  readonly is_seen: boolean;
  readonly action_url?: string;
  readonly metadata: Record<string, unknown>;
  readonly expires_at?: string;
}

// Notification preferences
export interface NotificationPreferences {
  readonly email_enabled: boolean;
  readonly push_enabled: boolean;
  readonly types: Record<
    NotificationType,
    {
      readonly email: boolean;
      readonly push: boolean;
      readonly in_app: boolean;
    }
  >;
}

// User follow relationship
export interface UserFollow extends BaseEntity, Timestamps {
  readonly follower_id: number;
  readonly following_id: number;
  readonly follower: UserListItem;
  readonly following: UserListItem;
}

// User block relationship
export interface UserBlock extends BaseEntity, Timestamps {
  readonly blocker_id: number;
  readonly blocked_id: number;
  readonly reason?: string;
}

// User report
export interface UserReport extends BaseEntity, Timestamps {
  readonly reporter_id: number;
  readonly reported_id: number;
  readonly reason: string;
  readonly description: string;
  readonly status: "pending" | "reviewed" | "resolved" | "dismissed";
  readonly admin_notes?: string;
  readonly resolved_at?: string;
  readonly resolved_by?: number;
}

// User badge types
export enum BadgeType {
  EARLY_ADOPTER = "early_adopter",
  PROLIFIC_WRITER = "prolific_writer",
  HELPFUL_COMMENTER = "helpful_commenter",
  COMMUNITY_LEADER = "community_leader",
  VERIFIED_AUTHOR = "verified_author",
  TOP_CONTRIBUTOR = "top_contributor",
}

// User badge
export interface UserBadge extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly badge_type: BadgeType;
  readonly name: string;
  readonly description: string;
  readonly icon: string;
  readonly color: string;
  readonly earned_at: string;
}

// User achievement
export interface UserAchievement extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly achievement_type: string;
  readonly name: string;
  readonly description: string;
  readonly points: number;
  readonly unlocked_at: string;
  readonly metadata: Record<string, unknown>;
}

// User subscription
export interface UserSubscription extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly plan_name: string;
  readonly status: "active" | "inactive" | "cancelled" | "expired";
  readonly starts_at: string;
  readonly ends_at?: string;
  readonly auto_renew: boolean;
  readonly features: string[];
}

// User analytics summary
export interface UserAnalyticsSummary {
  readonly user_id: number;
  readonly period: "day" | "week" | "month" | "year";
  readonly start_date: string;
  readonly end_date: string;
  readonly metrics: {
    readonly profile_views: number;
    readonly posts_created: number;
    readonly comments_made: number;
    readonly likes_received: number;
    readonly shares_received: number;
    readonly followers_gained: number;
    readonly engagement_rate: number;
  };
}

// User export data
export interface UserExportData {
  readonly user: UserDetails;
  readonly posts: Array<{
    readonly id: number;
    readonly title: string;
    readonly created_at: string;
  }>;
  readonly comments: Array<{
    readonly id: number;
    readonly content: string;
    readonly created_at: string;
  }>;
  readonly activities: UserActivity[];
  readonly notifications: UserNotification[];
}

// User import data
export interface UserImportData {
  readonly username: string;
  readonly email: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly role: UserRole;
  readonly profile?: Partial<ProfileUpdateRequest>;
}
