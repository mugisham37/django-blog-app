/**
 * Blog-related types and interfaces
 */

export enum PostStatus {
  DRAFT = "draft",
  PUBLISHED = "published",
  SCHEDULED = "scheduled",
  ARCHIVED = "archived",
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  parent: number | null;
  post_count: number;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
  description: string;
  post_count: number;
  created_at: string;
}

export interface Post {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  featured_image: string | null;
  author: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    avatar: string | null;
  };
  category: Category | null;
  tags: Tag[];
  status: PostStatus;
  is_featured: boolean;
  view_count: number;
  comment_count: number;
  like_count: number;
  published_at: string | null;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
  meta: PostMeta;
}

export interface PostMeta {
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string[];
  canonical_url?: string;
  reading_time?: number;
}

export interface CreatePostRequest {
  title: string;
  content: string;
  excerpt?: string;
  category_id?: number;
  tag_ids?: number[];
  status?: PostStatus;
  is_featured?: boolean;
  featured_image?: File;
  published_at?: string;
  scheduled_at?: string;
  meta?: Partial<PostMeta>;
}

export interface UpdatePostRequest extends Partial<CreatePostRequest> {
  id: number;
}

export interface PostListParams {
  page?: number;
  per_page?: number;
  status?: PostStatus;
  category?: string;
  tag?: string;
  author?: string;
  search?: string;
  ordering?: string;
  featured?: boolean;
}

export interface Comment {
  id: number;
  post: number;
  author: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    avatar: string | null;
  } | null;
  parent: number | null;
  content: string;
  is_approved: boolean;
  like_count: number;
  reply_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCommentRequest {
  post_id: number;
  content: string;
  parent_id?: number;
  author_name?: string;
  author_email?: string;
}

export interface UpdateCommentRequest {
  content: string;
}

export interface CommentListParams {
  page?: number;
  per_page?: number;
  post_id?: number;
  parent_id?: number;
  approved?: boolean;
  ordering?: string;
}

export interface CreateCategoryRequest {
  name: string;
  description?: string;
  parent_id?: number;
}

export interface UpdateCategoryRequest extends Partial<CreateCategoryRequest> {
  id: number;
}

export interface CreateTagRequest {
  name: string;
  description?: string;
}

export interface UpdateTagRequest extends Partial<CreateTagRequest> {
  id: number;
}
