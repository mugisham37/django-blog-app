/**
 * Blog-related type definitions
 */

import { BaseEntity, Timestamps, Visibility, Status } from "./common";
import { UserListItem } from "./user";

// Post status
export enum PostStatus {
  DRAFT = "draft",
  PUBLISHED = "published",
  SCHEDULED = "scheduled",
  ARCHIVED = "archived",
  DELETED = "deleted",
}

// Content format
export enum ContentFormat {
  MARKDOWN = "markdown",
  HTML = "html",
  RICH_TEXT = "rich_text",
  PLAIN_TEXT = "plain_text",
}

// Category interface
export interface Category extends BaseEntity, Timestamps {
  readonly name: string;
  readonly slug: string;
  readonly description?: string;
  readonly color?: string;
  readonly icon?: string;
  readonly parent_id?: number;
  readonly parent?: Category;
  readonly children?: Category[];
  readonly posts_count: number;
  readonly is_featured: boolean;
  readonly sort_order: number;
}

// Tag interface
export interface Tag extends BaseEntity, Timestamps {
  readonly name: string;
  readonly slug: string;
  readonly description?: string;
  readonly color?: string;
  readonly posts_count: number;
  readonly is_trending: boolean;
}

// Post SEO metadata
export interface PostSEO {
  readonly meta_title?: string;
  readonly meta_description?: string;
  readonly meta_keywords?: string[];
  readonly og_title?: string;
  readonly og_description?: string;
  readonly og_image?: string;
  readonly twitter_title?: string;
  readonly twitter_description?: string;
  readonly twitter_image?: string;
  readonly canonical_url?: string;
  readonly robots_index: boolean;
  readonly robots_follow: boolean;
}

// Post media
export interface PostMedia extends BaseEntity, Timestamps {
  readonly post_id: number;
  readonly type: "image" | "video" | "audio" | "document";
  readonly url: string;
  readonly thumbnail_url?: string;
  readonly title?: string;
  readonly description?: string;
  readonly alt_text?: string;
  readonly file_size: number;
  readonly mime_type: string;
  readonly width?: number;
  readonly height?: number;
  readonly duration?: number;
  readonly sort_order: number;
}

// Post interface
export interface Post extends BaseEntity, Timestamps {
  readonly title: string;
  readonly slug: string;
  readonly excerpt?: string;
  readonly content: string;
  readonly content_format: ContentFormat;
  readonly featured_image?: string;
  readonly featured_image_alt?: string;
  readonly author_id: number;
  readonly author: UserListItem;
  readonly category_id?: number;
  readonly category?: Category;
  readonly tags: Tag[];
  readonly status: PostStatus;
  readonly visibility: Visibility;
  readonly is_featured: boolean;
  readonly is_pinned: boolean;
  readonly allow_comments: boolean;
  readonly published_at?: string;
  readonly scheduled_at?: string;
  readonly reading_time: number;
  readonly view_count: number;
  readonly like_count: number;
  readonly comment_count: number;
  readonly share_count: number;
  readonly seo: PostSEO;
  readonly media: PostMedia[];
}

// Post list item (for listings)
export interface PostListItem {
  readonly id: number;
  readonly title: string;
  readonly slug: string;
  readonly excerpt?: string;
  readonly featured_image?: string;
  readonly author: UserListItem;
  readonly category?: Category;
  readonly tags: Tag[];
  readonly status: PostStatus;
  readonly is_featured: boolean;
  readonly published_at?: string;
  readonly reading_time: number;
  readonly view_count: number;
  readonly like_count: number;
  readonly comment_count: number;
  readonly created_at: string;
  readonly updated_at: string;
}

// Post creation request
export interface PostCreateRequest {
  readonly title: string;
  readonly slug?: string;
  readonly excerpt?: string;
  readonly content: string;
  readonly content_format: ContentFormat;
  readonly featured_image?: File | string;
  readonly featured_image_alt?: string;
  readonly category_id?: number;
  readonly tag_ids?: number[];
  readonly status: PostStatus;
  readonly visibility: Visibility;
  readonly is_featured?: boolean;
  readonly allow_comments?: boolean;
  readonly published_at?: string;
  readonly scheduled_at?: string;
  readonly seo?: Partial<PostSEO>;
}

// Post update request
export interface PostUpdateRequest {
  readonly title?: string;
  readonly slug?: string;
  readonly excerpt?: string;
  readonly content?: string;
  readonly content_format?: ContentFormat;
  readonly featured_image?: File | string;
  readonly featured_image_alt?: string;
  readonly category_id?: number;
  readonly tag_ids?: number[];
  readonly status?: PostStatus;
  readonly visibility?: Visibility;
  readonly is_featured?: boolean;
  readonly allow_comments?: boolean;
  readonly published_at?: string;
  readonly scheduled_at?: string;
  readonly seo?: Partial<PostSEO>;
}

// Post search filters
export interface PostSearchFilters {
  readonly author_id?: number;
  readonly category_id?: number;
  readonly tag_ids?: number[];
  readonly status?: PostStatus[];
  readonly visibility?: Visibility[];
  readonly is_featured?: boolean;
  readonly published_after?: string;
  readonly published_before?: string;
  readonly created_after?: string;
  readonly created_before?: string;
}

// Post analytics
export interface PostAnalytics {
  readonly post_id: number;
  readonly period: "day" | "week" | "month" | "year";
  readonly start_date: string;
  readonly end_date: string;
  readonly metrics: {
    readonly views: number;
    readonly unique_views: number;
    readonly likes: number;
    readonly comments: number;
    readonly shares: number;
    readonly reading_time_avg: number;
    readonly bounce_rate: number;
    readonly engagement_rate: number;
  };
  readonly traffic_sources: Array<{
    readonly source: string;
    readonly views: number;
    readonly percentage: number;
  }>;
  readonly popular_sections: Array<{
    readonly section: string;
    readonly time_spent: number;
  }>;
}

// Post revision
export interface PostRevision extends BaseEntity, Timestamps {
  readonly post_id: number;
  readonly title: string;
  readonly content: string;
  readonly excerpt?: string;
  readonly author_id: number;
  readonly author: UserListItem;
  readonly change_summary?: string;
  readonly is_major: boolean;
  readonly version: number;
}

// Post like
export interface PostLike extends BaseEntity, Timestamps {
  readonly post_id: number;
  readonly user_id: number;
  readonly user: UserListItem;
}

// Post share
export interface PostShare extends BaseEntity, Timestamps {
  readonly post_id: number;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly platform:
    | "facebook"
    | "twitter"
    | "linkedin"
    | "email"
    | "copy_link"
    | "other";
  readonly ip_address: string;
  readonly user_agent: string;
}

// Post view
export interface PostView extends BaseEntity, Timestamps {
  readonly post_id: number;
  readonly user_id?: number;
  readonly user?: UserListItem;
  readonly ip_address: string;
  readonly user_agent: string;
  readonly referrer?: string;
  readonly reading_time: number;
  readonly scroll_depth: number;
}

// Related posts
export interface RelatedPost {
  readonly id: number;
  readonly title: string;
  readonly slug: string;
  readonly excerpt?: string;
  readonly featured_image?: string;
  readonly author: UserListItem;
  readonly published_at: string;
  readonly reading_time: number;
  readonly similarity_score: number;
}

// Post series
export interface PostSeries extends BaseEntity, Timestamps {
  readonly name: string;
  readonly slug: string;
  readonly description?: string;
  readonly cover_image?: string;
  readonly author_id: number;
  readonly author: UserListItem;
  readonly posts: PostListItem[];
  readonly posts_count: number;
  readonly is_completed: boolean;
}

// Category creation request
export interface CategoryCreateRequest {
  readonly name: string;
  readonly slug?: string;
  readonly description?: string;
  readonly color?: string;
  readonly icon?: string;
  readonly parent_id?: number;
  readonly is_featured?: boolean;
  readonly sort_order?: number;
}

// Tag creation request
export interface TagCreateRequest {
  readonly name: string;
  readonly slug?: string;
  readonly description?: string;
  readonly color?: string;
}

// Blog statistics
export interface BlogStats {
  readonly total_posts: number;
  readonly published_posts: number;
  readonly draft_posts: number;
  readonly total_categories: number;
  readonly total_tags: number;
  readonly total_views: number;
  readonly total_likes: number;
  readonly total_comments: number;
  readonly total_shares: number;
  readonly popular_posts: PostListItem[];
  readonly popular_categories: Array<
    Category & { readonly posts_count: number }
  >;
  readonly popular_tags: Array<Tag & { readonly posts_count: number }>;
}
