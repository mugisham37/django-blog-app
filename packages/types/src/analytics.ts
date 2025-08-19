/**
 * Analytics-related type definitions
 */

import { BaseEntity, Timestamps } from "./common";
import { UserListItem } from "./user";

// Analytics event types
export enum AnalyticsEventType {
  PAGE_VIEW = "page_view",
  POST_VIEW = "post_view",
  POST_LIKE = "post_like",
  POST_SHARE = "post_share",
  COMMENT_CREATE = "comment_create",
  USER_REGISTER = "user_register",
  USER_LOGIN = "user_login",
  SEARCH_QUERY = "search_query",
  NEWSLETTER_SUBSCRIBE = "newsletter_subscribe",
  DOWNLOAD = "download",
  CLICK = "click",
  FORM_SUBMIT = "form_submit",
  ERROR = "error",
}

// Device types
export enum DeviceType {
  DESKTOP = "desktop",
  MOBILE = "mobile",
  TABLET = "tablet",
  TV = "tv",
  WEARABLE = "wearable",
  UNKNOWN = "unknown",
}

// Browser types
export enum BrowserType {
  CHROME = "chrome",
  FIREFOX = "firefox",
  SAFARI = "safari",
  EDGE = "edge",
  OPERA = "opera",
  IE = "ie",
  OTHER = "other",
}

// Operating system types
export enum OSType {
  WINDOWS = "windows",
  MACOS = "macos",
  LINUX = "linux",
  ANDROID = "android",
  IOS = "ios",
  OTHER = "other",
}

// Traffic source types
export enum TrafficSource {
  DIRECT = "direct",
  SEARCH = "search",
  SOCIAL = "social",
  EMAIL = "email",
  REFERRAL = "referral",
  PAID = "paid",
  OTHER = "other",
}

// Page view analytics
export interface PageView extends BaseEntity, Timestamps {
  readonly url: string;
  readonly title?: string;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly session_id: string;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly referrer?: string;
  readonly utm_source?: string;
  readonly utm_medium?: string;
  readonly utm_campaign?: string;
  readonly utm_term?: string;
  readonly utm_content?: string;
  readonly device_type: DeviceType;
  readonly browser: BrowserType;
  readonly os: OSType;
  readonly screen_resolution?: string;
  readonly viewport_size?: string;
  readonly language: string;
  readonly country?: string;
  readonly city?: string;
  readonly duration?: number;
  readonly bounce: boolean;
}

// Search query analytics
export interface SearchQuery extends BaseEntity, Timestamps {
  readonly query: string;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly session_id: string;
  readonly ip_address: string;
  readonly results_count: number;
  readonly clicked_result?: number;
  readonly no_results: boolean;
  readonly filters_used: Record<string, unknown>;
  readonly sort_order?: string;
}

// User activity analytics
export interface UserActivity extends BaseEntity, Timestamps {
  readonly user_id: number;
  readonly user: UserListItem;
  readonly event_type: AnalyticsEventType;
  readonly event_data: Record<string, unknown>;
  readonly session_id: string;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly page_url: string;
  readonly referrer?: string;
}

// Conversion event
export interface ConversionEvent extends BaseEntity, Timestamps {
  readonly event_name: string;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly session_id: string;
  readonly value?: number;
  readonly currency?: string;
  readonly properties: Record<string, unknown>;
  readonly funnel_step?: number;
  readonly attribution_source?: string;
}

// Analytics dashboard metrics
export interface DashboardMetrics {
  readonly period:
    | "today"
    | "yesterday"
    | "week"
    | "month"
    | "quarter"
    | "year";
  readonly start_date: string;
  readonly end_date: string;
  readonly metrics: {
    readonly total_visitors: number;
    readonly unique_visitors: number;
    readonly page_views: number;
    readonly bounce_rate: number;
    readonly avg_session_duration: number;
    readonly new_users: number;
    readonly returning_users: number;
    readonly conversion_rate: number;
  };
  readonly comparison?: {
    readonly period: string;
    readonly metrics: Record<string, number>;
    readonly changes: Record<
      string,
      {
        readonly value: number;
        readonly percentage: number;
        readonly trend: "up" | "down" | "stable";
      }
    >;
  };
}

// Traffic analytics
export interface TrafficAnalytics {
  readonly period: string;
  readonly start_date: string;
  readonly end_date: string;
  readonly sources: Array<{
    readonly source: TrafficSource;
    readonly name: string;
    readonly visitors: number;
    readonly page_views: number;
    readonly bounce_rate: number;
    readonly avg_duration: number;
    readonly conversion_rate: number;
  }>;
  readonly referrers: Array<{
    readonly domain: string;
    readonly visitors: number;
    readonly page_views: number;
  }>;
  readonly campaigns: Array<{
    readonly campaign: string;
    readonly source: string;
    readonly medium: string;
    readonly visitors: number;
    readonly conversions: number;
    readonly cost?: number;
    readonly roi?: number;
  }>;
}

// Content analytics
export interface ContentAnalytics {
  readonly period: string;
  readonly start_date: string;
  readonly end_date: string;
  readonly popular_pages: Array<{
    readonly url: string;
    readonly title: string;
    readonly page_views: number;
    readonly unique_views: number;
    readonly avg_duration: number;
    readonly bounce_rate: number;
    readonly exit_rate: number;
  }>;
  readonly popular_posts: Array<{
    readonly id: number;
    readonly title: string;
    readonly slug: string;
    readonly views: number;
    readonly likes: number;
    readonly comments: number;
    readonly shares: number;
    readonly engagement_rate: number;
  }>;
  readonly search_terms: Array<{
    readonly term: string;
    readonly searches: number;
    readonly results_clicked: number;
    readonly no_results: number;
  }>;
}

// User behavior analytics
export interface UserBehaviorAnalytics {
  readonly period: string;
  readonly start_date: string;
  readonly end_date: string;
  readonly user_flow: Array<{
    readonly step: number;
    readonly page: string;
    readonly users: number;
    readonly dropoff_rate: number;
  }>;
  readonly heatmap_data: Array<{
    readonly page: string;
    readonly clicks: Array<{
      readonly x: number;
      readonly y: number;
      readonly count: number;
    }>;
    readonly scrolls: Array<{
      readonly depth: number;
      readonly users: number;
    }>;
  }>;
  readonly session_recordings: Array<{
    readonly session_id: string;
    readonly user_id?: number;
    readonly duration: number;
    readonly pages_visited: number;
    readonly events_count: number;
    readonly recording_url: string;
  }>;
}

// Real-time analytics
export interface RealTimeAnalytics {
  readonly active_users: number;
  readonly active_sessions: number;
  readonly current_page_views: number;
  readonly top_pages: Array<{
    readonly url: string;
    readonly title: string;
    readonly active_users: number;
  }>;
  readonly traffic_sources: Array<{
    readonly source: string;
    readonly active_users: number;
  }>;
  readonly locations: Array<{
    readonly country: string;
    readonly city?: string;
    readonly active_users: number;
  }>;
  readonly events: Array<{
    readonly event_type: AnalyticsEventType;
    readonly count: number;
    readonly timestamp: string;
  }>;
}

// Analytics report
export interface AnalyticsReport {
  readonly id: number;
  readonly name: string;
  readonly description?: string;
  readonly report_type:
    | "traffic"
    | "content"
    | "user_behavior"
    | "conversion"
    | "custom";
  readonly filters: Record<string, unknown>;
  readonly metrics: string[];
  readonly dimensions: string[];
  readonly date_range: {
    readonly start_date: string;
    readonly end_date: string;
  };
  readonly schedule?: {
    readonly frequency: "daily" | "weekly" | "monthly";
    readonly recipients: string[];
    readonly format: "pdf" | "csv" | "json";
  };
  readonly created_by: number;
  readonly created_at: string;
  readonly updated_at: string;
}

// Analytics goal
export interface AnalyticsGoal {
  readonly id: number;
  readonly name: string;
  readonly description?: string;
  readonly goal_type: "page_views" | "conversions" | "revenue" | "engagement";
  readonly target_value: number;
  readonly current_value: number;
  readonly progress_percentage: number;
  readonly period: "daily" | "weekly" | "monthly" | "quarterly" | "yearly";
  readonly start_date: string;
  readonly end_date: string;
  readonly is_active: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

// A/B test analytics
export interface ABTestAnalytics {
  readonly test_id: string;
  readonly test_name: string;
  readonly variants: Array<{
    readonly variant_id: string;
    readonly variant_name: string;
    readonly traffic_percentage: number;
    readonly participants: number;
    readonly conversions: number;
    readonly conversion_rate: number;
    readonly confidence_level: number;
    readonly is_winner: boolean;
  }>;
  readonly status: "draft" | "running" | "paused" | "completed";
  readonly start_date: string;
  readonly end_date?: string;
  readonly statistical_significance: number;
}

// Custom analytics event
export interface CustomAnalyticsEvent {
  readonly event_name: string;
  readonly properties: Record<string, unknown>;
  readonly user_id?: number;
  readonly session_id?: string;
  readonly timestamp?: string;
}
