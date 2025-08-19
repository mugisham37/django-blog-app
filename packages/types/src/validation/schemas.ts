/**
 * JSON Schema definitions for API validation
 */

import { JSONSchema7 } from "json-schema";

// Base entity schema
export const BaseEntitySchema: JSONSchema7 = {
  type: "object",
  properties: {
    id: { type: "number", minimum: 1 },
    created_at: { type: "string", format: "date-time" },
    updated_at: { type: "string", format: "date-time" },
  },
  required: ["id", "created_at", "updated_at"],
};

// API Response schema
export const APIResponseSchema: JSONSchema7 = {
  type: "object",
  properties: {
    success: { type: "boolean" },
    data: {}, // Any type
    message: { type: "string" },
    errors: {
      type: "object",
      additionalProperties: {
        type: "array",
        items: { type: "string" },
      },
    },
    meta: {
      type: "object",
      additionalProperties: true,
    },
  },
  required: ["success", "data", "message"],
};

// Paginated Response schema
export const PaginatedResponseSchema: JSONSchema7 = {
  allOf: [
    APIResponseSchema,
    {
      type: "object",
      properties: {
        data: {
          type: "array",
        },
        pagination: {
          type: "object",
          properties: {
            page: { type: "number", minimum: 1 },
            pages: { type: "number", minimum: 1 },
            per_page: { type: "number", minimum: 1, maximum: 100 },
            total: { type: "number", minimum: 0 },
            has_next: { type: "boolean" },
            has_prev: { type: "boolean" },
          },
          required: [
            "page",
            "pages",
            "per_page",
            "total",
            "has_next",
            "has_prev",
          ],
        },
      },
      required: ["pagination"],
    },
  ],
};

// User schema
export const UserSchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        username: { type: "string", minLength: 3, maxLength: 30 },
        email: { type: "string", format: "email" },
        first_name: { type: "string", maxLength: 30 },
        last_name: { type: "string", maxLength: 30 },
        role: {
          type: "string",
          enum: [
            "admin",
            "moderator",
            "editor",
            "author",
            "subscriber",
            "guest",
          ],
        },
        status: {
          type: "string",
          enum: ["active", "inactive", "pending", "suspended", "banned"],
        },
        is_verified: { type: "boolean" },
        is_staff: { type: "boolean" },
        is_superuser: { type: "boolean" },
        last_login: { type: "string", format: "date-time" },
      },
      required: [
        "username",
        "email",
        "role",
        "status",
        "is_verified",
        "is_staff",
        "is_superuser",
      ],
    },
  ],
};

// Login request schema
export const LoginRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    email: { type: "string", format: "email" },
    password: { type: "string", minLength: 8 },
    remember_me: { type: "boolean" },
    mfa_code: { type: "string", pattern: "^[0-9]{6}$" },
  },
  required: ["email", "password"],
};

// Registration request schema
export const RegisterRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    username: {
      type: "string",
      minLength: 3,
      maxLength: 30,
      pattern: "^[a-zA-Z0-9_]+$",
    },
    email: { type: "string", format: "email" },
    password: { type: "string", minLength: 8 },
    password_confirm: { type: "string", minLength: 8 },
    first_name: { type: "string", maxLength: 30 },
    last_name: { type: "string", maxLength: 30 },
    terms_accepted: { type: "boolean", const: true },
    newsletter_opt_in: { type: "boolean" },
  },
  required: [
    "username",
    "email",
    "password",
    "password_confirm",
    "terms_accepted",
  ],
};

// Post schema
export const PostSchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        title: { type: "string", minLength: 1, maxLength: 200 },
        slug: { type: "string", pattern: "^[a-z0-9-]+$" },
        excerpt: { type: "string", maxLength: 500 },
        content: { type: "string", minLength: 1 },
        content_format: {
          type: "string",
          enum: ["markdown", "html", "rich_text", "plain_text"],
        },
        featured_image: { type: "string", format: "uri" },
        featured_image_alt: { type: "string", maxLength: 200 },
        author_id: { type: "number", minimum: 1 },
        category_id: { type: "number", minimum: 1 },
        status: {
          type: "string",
          enum: ["draft", "published", "scheduled", "archived", "deleted"],
        },
        visibility: {
          type: "string",
          enum: ["public", "private", "restricted", "draft"],
        },
        is_featured: { type: "boolean" },
        is_pinned: { type: "boolean" },
        allow_comments: { type: "boolean" },
        published_at: { type: "string", format: "date-time" },
        scheduled_at: { type: "string", format: "date-time" },
        reading_time: { type: "number", minimum: 0 },
        view_count: { type: "number", minimum: 0 },
        like_count: { type: "number", minimum: 0 },
        comment_count: { type: "number", minimum: 0 },
        share_count: { type: "number", minimum: 0 },
      },
      required: [
        "title",
        "slug",
        "content",
        "content_format",
        "author_id",
        "status",
        "visibility",
        "is_featured",
        "allow_comments",
        "reading_time",
      ],
    },
  ],
};

// Post create request schema
export const PostCreateRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    title: { type: "string", minLength: 1, maxLength: 200 },
    slug: { type: "string", pattern: "^[a-z0-9-]+$" },
    excerpt: { type: "string", maxLength: 500 },
    content: { type: "string", minLength: 1 },
    content_format: {
      type: "string",
      enum: ["markdown", "html", "rich_text", "plain_text"],
      default: "markdown",
    },
    featured_image_alt: { type: "string", maxLength: 200 },
    category_id: { type: "number", minimum: 1 },
    tag_ids: {
      type: "array",
      items: { type: "number", minimum: 1 },
      uniqueItems: true,
    },
    status: {
      type: "string",
      enum: ["draft", "published", "scheduled"],
      default: "draft",
    },
    visibility: {
      type: "string",
      enum: ["public", "private", "restricted", "draft"],
      default: "public",
    },
    is_featured: { type: "boolean", default: false },
    allow_comments: { type: "boolean", default: true },
    published_at: { type: "string", format: "date-time" },
    scheduled_at: { type: "string", format: "date-time" },
  },
  required: ["title", "content"],
};

// Category schema
export const CategorySchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        name: { type: "string", minLength: 1, maxLength: 100 },
        slug: { type: "string", pattern: "^[a-z0-9-]+$" },
        description: { type: "string", maxLength: 500 },
        color: { type: "string", pattern: "^#[0-9A-Fa-f]{6}$" },
        icon: { type: "string", maxLength: 50 },
        parent_id: { type: "number", minimum: 1 },
        posts_count: { type: "number", minimum: 0 },
        is_featured: { type: "boolean" },
        sort_order: { type: "number", minimum: 0 },
      },
      required: ["name", "slug", "posts_count", "is_featured", "sort_order"],
    },
  ],
};

// Tag schema
export const TagSchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        name: { type: "string", minLength: 1, maxLength: 50 },
        slug: { type: "string", pattern: "^[a-z0-9-]+$" },
        description: { type: "string", maxLength: 200 },
        color: { type: "string", pattern: "^#[0-9A-Fa-f]{6}$" },
        posts_count: { type: "number", minimum: 0 },
        is_trending: { type: "boolean" },
      },
      required: ["name", "slug", "posts_count", "is_trending"],
    },
  ],
};

// Comment schema
export const CommentSchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        content: { type: "string", minLength: 1, maxLength: 2000 },
        author_id: { type: "number", minimum: 1 },
        post_id: { type: "number", minimum: 1 },
        parent_id: { type: "number", minimum: 1 },
        status: {
          type: "string",
          enum: ["pending", "approved", "rejected", "spam"],
        },
        is_pinned: { type: "boolean" },
        like_count: { type: "number", minimum: 0 },
        reply_count: { type: "number", minimum: 0 },
      },
      required: ["content", "author_id", "post_id", "status", "is_pinned"],
    },
  ],
};

// Newsletter subscriber schema
export const NewsletterSubscriberSchema: JSONSchema7 = {
  allOf: [
    BaseEntitySchema,
    {
      type: "object",
      properties: {
        email: { type: "string", format: "email" },
        first_name: { type: "string", maxLength: 50 },
        last_name: { type: "string", maxLength: 50 },
        user_id: { type: "number", minimum: 1 },
        status: {
          type: "string",
          enum: [
            "active",
            "inactive",
            "pending",
            "unsubscribed",
            "bounced",
            "complained",
          ],
        },
        subscribed_at: { type: "string", format: "date-time" },
        unsubscribed_at: { type: "string", format: "date-time" },
        confirmed_at: { type: "string", format: "date-time" },
        bounce_count: { type: "number", minimum: 0 },
        complaint_count: { type: "number", minimum: 0 },
        tags: {
          type: "array",
          items: { type: "string" },
          uniqueItems: true,
        },
        source: { type: "string", maxLength: 100 },
        ip_address: { type: "string", format: "ipv4" },
        user_agent: { type: "string", maxLength: 500 },
      },
      required: [
        "email",
        "status",
        "subscribed_at",
        "bounce_count",
        "complaint_count",
        "tags",
        "source",
      ],
    },
  ],
};

// Newsletter subscription request schema
export const SubscriptionRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    email: { type: "string", format: "email" },
    first_name: { type: "string", maxLength: 50 },
    last_name: { type: "string", maxLength: 50 },
    tags: {
      type: "array",
      items: { type: "string" },
      uniqueItems: true,
    },
    source: { type: "string", maxLength: 100 },
    double_opt_in: { type: "boolean", default: true },
  },
  required: ["email"],
};

// Search request schema
export const SearchRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    query: { type: "string", minLength: 1, maxLength: 200 },
    page: { type: "number", minimum: 1, default: 1 },
    per_page: { type: "number", minimum: 1, maximum: 100, default: 20 },
    sort: {
      type: "array",
      items: {
        type: "object",
        properties: {
          field: { type: "string" },
          order: { type: "string", enum: ["asc", "desc"] },
        },
        required: ["field", "order"],
      },
    },
    filters: {
      type: "object",
      additionalProperties: true,
    },
    highlight: { type: "boolean", default: false },
    facets: {
      type: "array",
      items: { type: "string" },
      uniqueItems: true,
    },
  },
  required: ["query"],
};

// Bulk operation request schema
export const BulkOperationRequestSchema: JSONSchema7 = {
  type: "object",
  properties: {
    operation: { type: "string", enum: ["create", "update", "delete"] },
    items: {
      type: "array",
      minItems: 1,
      maxItems: 1000,
    },
    options: {
      type: "object",
      properties: {
        batch_size: { type: "number", minimum: 1, maximum: 100, default: 50 },
        continue_on_error: { type: "boolean", default: false },
      },
    },
  },
  required: ["operation", "items"],
};

// Export all schemas
export const schemas = {
  BaseEntitySchema,
  APIResponseSchema,
  PaginatedResponseSchema,
  UserSchema,
  LoginRequestSchema,
  RegisterRequestSchema,
  PostSchema,
  PostCreateRequestSchema,
  CategorySchema,
  TagSchema,
  CommentSchema,
  NewsletterSubscriberSchema,
  SubscriptionRequestSchema,
  SearchRequestSchema,
  BulkOperationRequestSchema,
};
