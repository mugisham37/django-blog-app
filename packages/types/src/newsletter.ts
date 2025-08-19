/**
 * Newsletter-related type definitions
 */

import { BaseEntity, Timestamps, Status } from "./common";
import { UserListItem } from "./user";

// Newsletter subscription status
export enum SubscriptionStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PENDING = "pending",
  UNSUBSCRIBED = "unsubscribed",
  BOUNCED = "bounced",
  COMPLAINED = "complained",
}

// Campaign status
export enum CampaignStatus {
  DRAFT = "draft",
  SCHEDULED = "scheduled",
  SENDING = "sending",
  SENT = "sent",
  PAUSED = "paused",
  CANCELLED = "cancelled",
  FAILED = "failed",
}

// Campaign type
export enum CampaignType {
  NEWSLETTER = "newsletter",
  PROMOTIONAL = "promotional",
  TRANSACTIONAL = "transactional",
  WELCOME = "welcome",
  ANNOUNCEMENT = "announcement",
  DIGEST = "digest",
}

// Email template type
export enum TemplateType {
  NEWSLETTER = "newsletter",
  WELCOME = "welcome",
  CONFIRMATION = "confirmation",
  PROMOTIONAL = "promotional",
  TRANSACTIONAL = "transactional",
  CUSTOM = "custom",
}

// Newsletter subscriber
export interface NewsletterSubscriber extends BaseEntity, Timestamps {
  readonly email: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly status: SubscriptionStatus;
  readonly subscribed_at: string;
  readonly unsubscribed_at?: string;
  readonly confirmed_at?: string;
  readonly bounce_count: number;
  readonly complaint_count: number;
  readonly tags: string[];
  readonly preferences: SubscriberPreferences;
  readonly source: string;
  readonly ip_address?: string;
  readonly user_agent?: string;
}

// Subscriber preferences
export interface SubscriberPreferences {
  readonly frequency: "daily" | "weekly" | "monthly" | "never";
  readonly categories: string[];
  readonly format: "html" | "text";
  readonly language: string;
  readonly timezone: string;
}

// Newsletter subscription request
export interface SubscriptionRequest {
  readonly email: string;
  readonly first_name?: string;
  readonly last_name?: string;
  readonly preferences?: Partial<SubscriberPreferences>;
  readonly tags?: string[];
  readonly source?: string;
  readonly double_opt_in?: boolean;
}

// Newsletter unsubscription request
export interface UnsubscriptionRequest {
  readonly email?: string;
  readonly token?: string;
  readonly reason?: string;
  readonly feedback?: string;
}

// Email template
export interface EmailTemplate extends BaseEntity, Timestamps {
  readonly name: string;
  readonly subject: string;
  readonly html_content: string;
  readonly text_content?: string;
  readonly template_type: TemplateType;
  readonly is_active: boolean;
  readonly variables: TemplateVariable[];
  readonly preview_text?: string;
  readonly from_name?: string;
  readonly from_email?: string;
  readonly reply_to?: string;
  readonly tags: string[];
}

// Template variable
export interface TemplateVariable {
  readonly name: string;
  readonly type: "text" | "number" | "date" | "boolean" | "url" | "email";
  readonly description?: string;
  readonly default_value?: string;
  readonly required: boolean;
}

// Newsletter campaign
export interface NewsletterCampaign extends BaseEntity, Timestamps {
  readonly name: string;
  readonly subject: string;
  readonly html_content: string;
  readonly text_content?: string;
  readonly template_id?: number;
  readonly template?: EmailTemplate;
  readonly campaign_type: CampaignType;
  readonly status: CampaignStatus;
  readonly from_name: string;
  readonly from_email: string;
  readonly reply_to?: string;
  readonly preview_text?: string;
  readonly scheduled_at?: string;
  readonly sent_at?: string;
  readonly recipient_count: number;
  readonly delivered_count: number;
  readonly opened_count: number;
  readonly clicked_count: number;
  readonly bounced_count: number;
  readonly complained_count: number;
  readonly unsubscribed_count: number;
  readonly tags: string[];
  readonly segments: CampaignSegment[];
  readonly tracking_settings: TrackingSettings;
}

// Campaign segment
export interface CampaignSegment {
  readonly name: string;
  readonly conditions: SegmentCondition[];
  readonly subscriber_count: number;
}

// Segment condition
export interface SegmentCondition {
  readonly field: string;
  readonly operator:
    | "equals"
    | "not_equals"
    | "contains"
    | "not_contains"
    | "starts_with"
    | "ends_with"
    | "in"
    | "not_in";
  readonly value: string | string[];
}

// Tracking settings
export interface TrackingSettings {
  readonly open_tracking: boolean;
  readonly click_tracking: boolean;
  readonly unsubscribe_tracking: boolean;
  readonly google_analytics: boolean;
  readonly custom_domain?: string;
}

// Campaign creation request
export interface CampaignCreateRequest {
  readonly name: string;
  readonly subject: string;
  readonly html_content?: string;
  readonly text_content?: string;
  readonly template_id?: number;
  readonly campaign_type: CampaignType;
  readonly from_name: string;
  readonly from_email: string;
  readonly reply_to?: string;
  readonly preview_text?: string;
  readonly scheduled_at?: string;
  readonly tags?: string[];
  readonly segments?: CampaignSegment[];
  readonly tracking_settings?: Partial<TrackingSettings>;
}

// Campaign analytics
export interface CampaignAnalytics {
  readonly campaign_id: number;
  readonly campaign_name: string;
  readonly sent_at: string;
  readonly metrics: {
    readonly recipients: number;
    readonly delivered: number;
    readonly delivery_rate: number;
    readonly opened: number;
    readonly open_rate: number;
    readonly clicked: number;
    readonly click_rate: number;
    readonly bounced: number;
    readonly bounce_rate: number;
    readonly complained: number;
    readonly complaint_rate: number;
    readonly unsubscribed: number;
    readonly unsubscribe_rate: number;
  };
  readonly timeline: Array<{
    readonly timestamp: string;
    readonly event:
      | "sent"
      | "delivered"
      | "opened"
      | "clicked"
      | "bounced"
      | "complained"
      | "unsubscribed";
    readonly count: number;
  }>;
  readonly top_links: Array<{
    readonly url: string;
    readonly clicks: number;
    readonly unique_clicks: number;
  }>;
  readonly geographic_data: Array<{
    readonly country: string;
    readonly opens: number;
    readonly clicks: number;
  }>;
  readonly device_data: Array<{
    readonly device_type: string;
    readonly opens: number;
    readonly clicks: number;
  }>;
}

// Email event
export interface EmailEvent extends BaseEntity, Timestamps {
  readonly campaign_id?: number;
  readonly subscriber_id: number;
  readonly subscriber: NewsletterSubscriber;
  readonly event_type:
    | "sent"
    | "delivered"
    | "opened"
    | "clicked"
    | "bounced"
    | "complained"
    | "unsubscribed";
  readonly email_address: string;
  readonly ip_address?: string;
  readonly user_agent?: string;
  readonly url?: string; // For click events
  readonly bounce_reason?: string; // For bounce events
  readonly complaint_reason?: string; // For complaint events
  readonly metadata: Record<string, unknown>;
}

// Newsletter list
export interface NewsletterList extends BaseEntity, Timestamps {
  readonly name: string;
  readonly description?: string;
  readonly is_active: boolean;
  readonly subscriber_count: number;
  readonly default_from_name: string;
  readonly default_from_email: string;
  readonly default_reply_to?: string;
  readonly tags: string[];
}

// Automation workflow
export interface AutomationWorkflow extends BaseEntity, Timestamps {
  readonly name: string;
  readonly description?: string;
  readonly trigger: WorkflowTrigger;
  readonly steps: WorkflowStep[];
  readonly is_active: boolean;
  readonly subscriber_count: number;
  readonly completion_rate: number;
}

// Workflow trigger
export interface WorkflowTrigger {
  readonly type: "subscription" | "tag_added" | "date" | "behavior" | "api";
  readonly conditions: Record<string, unknown>;
  readonly delay?: number; // in minutes
}

// Workflow step
export interface WorkflowStep {
  readonly id: string;
  readonly type: "email" | "delay" | "condition" | "tag" | "webhook";
  readonly config: Record<string, unknown>;
  readonly next_step_id?: string;
  readonly condition_steps?: Array<{
    readonly condition: string;
    readonly next_step_id: string;
  }>;
}

// Newsletter statistics
export interface NewsletterStats {
  readonly total_subscribers: number;
  readonly active_subscribers: number;
  readonly growth_rate: number;
  readonly churn_rate: number;
  readonly avg_open_rate: number;
  readonly avg_click_rate: number;
  readonly avg_unsubscribe_rate: number;
  readonly top_performing_campaigns: Array<{
    readonly campaign_id: number;
    readonly campaign_name: string;
    readonly open_rate: number;
    readonly click_rate: number;
  }>;
  readonly subscriber_growth: Array<{
    readonly date: string;
    readonly new_subscribers: number;
    readonly unsubscribes: number;
    readonly net_growth: number;
  }>;
}

// A/B test for campaigns
export interface CampaignABTest extends BaseEntity, Timestamps {
  readonly campaign_id: number;
  readonly test_name: string;
  readonly test_type: "subject" | "content" | "from_name" | "send_time";
  readonly variants: Array<{
    readonly variant_id: string;
    readonly name: string;
    readonly content: Record<string, unknown>;
    readonly traffic_percentage: number;
    readonly metrics: {
      readonly sent: number;
      readonly opened: number;
      readonly clicked: number;
      readonly open_rate: number;
      readonly click_rate: number;
    };
  }>;
  readonly winner_variant_id?: string;
  readonly confidence_level: number;
  readonly is_completed: boolean;
}

// Deliverability report
export interface DeliverabilityReport {
  readonly period: string;
  readonly start_date: string;
  readonly end_date: string;
  readonly overall_metrics: {
    readonly delivery_rate: number;
    readonly bounce_rate: number;
    readonly complaint_rate: number;
    readonly unsubscribe_rate: number;
    readonly reputation_score: number;
  };
  readonly by_domain: Array<{
    readonly domain: string;
    readonly sent: number;
    readonly delivered: number;
    readonly bounced: number;
    readonly delivery_rate: number;
  }>;
  readonly bounce_analysis: Array<{
    readonly bounce_type: "hard" | "soft";
    readonly reason: string;
    readonly count: number;
  }>;
  readonly recommendations: string[];
}
