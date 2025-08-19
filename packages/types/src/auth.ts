/**
 * Authentication and authorization type definitions
 */

import { BaseEntity, Timestamps } from "./common";

// User roles
export enum UserRole {
  ADMIN = "admin",
  MODERATOR = "moderator",
  EDITOR = "editor",
  AUTHOR = "author",
  SUBSCRIBER = "subscriber",
  GUEST = "guest",
}

// User status
export enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PENDING = "pending",
  SUSPENDED = "suspended",
  BANNED = "banned",
}

// Permission types
export enum Permission {
  // User management
  USER_CREATE = "user.create",
  USER_READ = "user.read",
  USER_UPDATE = "user.update",
  USER_DELETE = "user.delete",
  USER_LIST = "user.list",

  // Blog management
  POST_CREATE = "post.create",
  POST_READ = "post.read",
  POST_UPDATE = "post.update",
  POST_DELETE = "post.delete",
  POST_PUBLISH = "post.publish",
  POST_LIST = "post.list",

  // Comment management
  COMMENT_CREATE = "comment.create",
  COMMENT_READ = "comment.read",
  COMMENT_UPDATE = "comment.update",
  COMMENT_DELETE = "comment.delete",
  COMMENT_MODERATE = "comment.moderate",

  // Analytics
  ANALYTICS_READ = "analytics.read",
  ANALYTICS_EXPORT = "analytics.export",

  // Newsletter
  NEWSLETTER_CREATE = "newsletter.create",
  NEWSLETTER_SEND = "newsletter.send",
  NEWSLETTER_MANAGE = "newsletter.manage",

  // System administration
  SYSTEM_CONFIG = "system.config",
  SYSTEM_MONITOR = "system.monitor",
  SYSTEM_BACKUP = "system.backup",
}

// Authentication provider types
export enum AuthProvider {
  LOCAL = "local",
  GOOGLE = "google",
  FACEBOOK = "facebook",
  TWITTER = "twitter",
  GITHUB = "github",
  LINKEDIN = "linkedin",
}

// MFA method types
export enum MFAMethod {
  TOTP = "totp",
  SMS = "sms",
  EMAIL = "email",
  BACKUP_CODES = "backup_codes",
}

// User profile interface
export interface UserProfile extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly avatar?: string;
  readonly bio?: string;
  readonly website?: string;
  readonly location?: string;
  readonly birth_date?: string;
  readonly phone_number?: string;
  readonly social_links: Record<string, string>;
  readonly preferences: UserPreferences;
  readonly privacy_settings: PrivacySettings;
}

// User preferences
export interface UserPreferences {
  readonly language: string;
  readonly timezone: string;
  readonly theme: "light" | "dark" | "auto";
  readonly email_notifications: EmailNotificationSettings;
  readonly push_notifications: PushNotificationSettings;
}

// Email notification settings
export interface EmailNotificationSettings {
  readonly new_posts: boolean;
  readonly new_comments: boolean;
  readonly newsletter: boolean;
  readonly security_alerts: boolean;
  readonly marketing: boolean;
}

// Push notification settings
export interface PushNotificationSettings {
  readonly enabled: boolean;
  readonly new_posts: boolean;
  readonly new_comments: boolean;
  readonly mentions: boolean;
}

// Privacy settings
export interface PrivacySettings {
  readonly profile_visibility: "public" | "private" | "friends";
  readonly email_visibility: boolean;
  readonly activity_visibility: boolean;
  readonly search_indexing: boolean;
}

// User interface
export interface User extends BaseEntity, Timestamps {
  readonly username: string;
  readonly email: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly role: UserRole;
  readonly status: UserStatus;
  readonly is_verified: boolean;
  readonly is_staff: boolean;
  readonly is_superuser: boolean;
  readonly last_login?: string;
  readonly profile?: UserProfile;
  readonly permissions: Permission[];
}

// Login request
export interface LoginRequest {
  readonly email: string;
  readonly password: string;
  readonly remember_me?: boolean;
  readonly mfa_code?: string;
}

// Registration request
export interface RegisterRequest {
  readonly username: string;
  readonly email: string;
  readonly password: string;
  readonly password_confirm: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly terms_accepted: boolean;
  readonly newsletter_opt_in?: boolean;
}

// Password reset request
export interface PasswordResetRequest {
  readonly email: string;
}

// Password reset confirm
export interface PasswordResetConfirm {
  readonly token: string;
  readonly password: string;
  readonly password_confirm: string;
}

// Change password request
export interface ChangePasswordRequest {
  readonly current_password: string;
  readonly new_password: string;
  readonly new_password_confirm: string;
}

// JWT token payload
export interface JWTPayload {
  readonly user_id: number;
  readonly username: string;
  readonly email: string;
  readonly role: UserRole;
  readonly permissions: Permission[];
  readonly iat: number;
  readonly exp: number;
  readonly jti: string;
}

// OAuth2 authorization request
export interface OAuth2AuthRequest {
  readonly provider: AuthProvider;
  readonly redirect_uri: string;
  readonly state?: string;
  readonly scope?: string[];
}

// OAuth2 callback data
export interface OAuth2CallbackData {
  readonly provider: AuthProvider;
  readonly code: string;
  readonly state?: string;
  readonly error?: string;
  readonly error_description?: string;
}

// MFA setup request
export interface MFASetupRequest {
  readonly method: MFAMethod;
  readonly phone_number?: string; // For SMS
  readonly email?: string; // For email
}

// MFA setup response
export interface MFASetupResponse {
  readonly method: MFAMethod;
  readonly secret?: string; // For TOTP
  readonly qr_code?: string; // For TOTP
  readonly backup_codes?: string[]; // For backup codes
}

// MFA verification request
export interface MFAVerificationRequest {
  readonly method: MFAMethod;
  readonly code: string;
}

// Session information
export interface SessionInfo {
  readonly session_id: string;
  readonly user_id: number;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly location?: string;
  readonly device_type: "desktop" | "mobile" | "tablet";
  readonly is_current: boolean;
  readonly created_at: string;
  readonly last_activity: string;
  readonly expires_at: string;
}

// Security event types
export enum SecurityEventType {
  LOGIN_SUCCESS = "login_success",
  LOGIN_FAILED = "login_failed",
  LOGOUT = "logout",
  PASSWORD_CHANGED = "password_changed",
  EMAIL_CHANGED = "email_changed",
  MFA_ENABLED = "mfa_enabled",
  MFA_DISABLED = "mfa_disabled",
  ACCOUNT_LOCKED = "account_locked",
  ACCOUNT_UNLOCKED = "account_unlocked",
  SUSPICIOUS_ACTIVITY = "suspicious_activity",
}

// Security event
export interface SecurityEvent extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly event_type: SecurityEventType;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly location?: string;
  readonly details: Record<string, unknown>;
  readonly risk_score: number;
}

// Role definition
export interface Role extends BaseEntity, Timestamps {
  readonly name: string;
  readonly description: string;
  readonly permissions: Permission[];
  readonly is_system: boolean;
}

// Permission check request
export interface PermissionCheckRequest {
  readonly user_id: number;
  readonly permission: Permission;
  readonly resource_id?: number;
  readonly context?: Record<string, unknown>;
}

// Permission check response
export interface PermissionCheckResponse {
  readonly allowed: boolean;
  readonly reason?: string;
}

// Account verification
export interface AccountVerification {
  readonly token: string;
  readonly email: string;
  readonly expires_at: string;
}

// Password policy
export interface PasswordPolicy {
  readonly min_length: number;
  readonly max_length: number;
  readonly require_uppercase: boolean;
  readonly require_lowercase: boolean;
  readonly require_numbers: boolean;
  readonly require_symbols: boolean;
  readonly prevent_common: boolean;
  readonly prevent_personal: boolean;
  readonly history_count: number;
  readonly max_age_days: number;
}
