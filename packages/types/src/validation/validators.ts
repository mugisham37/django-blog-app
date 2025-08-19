/**
 * Validation utilities using Zod and AJV
 */

import Ajv, { JSONSchemaType, ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import { z } from "zod";
import { schemas } from "./schemas";

// Initialize AJV with formats
const ajv = new Ajv({ allErrors: true, removeAdditional: true });
addFormats(ajv);

// Compile schemas
const compiledSchemas = new Map<string, ValidateFunction>();

// Compile all schemas on initialization
Object.entries(schemas).forEach(([name, schema]) => {
  try {
    const validator = ajv.compile(schema);
    compiledSchemas.set(name, validator);
  } catch (error) {
    console.error(`Failed to compile schema ${name}:`, error);
  }
});

// Validation result interface
export interface ValidationResult<T = unknown> {
  readonly success: boolean;
  readonly data?: T;
  readonly errors?: Array<{
    readonly field: string;
    readonly message: string;
    readonly code: string;
  }>;
}

// Generic validator function
export function validateWithSchema<T = unknown>(
  schemaName: string,
  data: unknown
): ValidationResult<T> {
  const validator = compiledSchemas.get(schemaName);

  if (!validator) {
    return {
      success: false,
      errors: [
        {
          field: "schema",
          message: `Schema ${schemaName} not found`,
          code: "SCHEMA_NOT_FOUND",
        },
      ],
    };
  }

  const isValid = validator(data);

  if (isValid) {
    return {
      success: true,
      data: data as T,
    };
  }

  const errors =
    validator.errors?.map((error) => ({
      field: error.instancePath || error.schemaPath,
      message: error.message || "Validation error",
      code: error.keyword?.toUpperCase() || "VALIDATION_ERROR",
    })) || [];

  return {
    success: false,
    errors,
  };
}

// Create validator function for a specific schema
export function createValidator<T = unknown>(schemaName: string) {
  return (data: unknown): ValidationResult<T> => {
    return validateWithSchema<T>(schemaName, data);
  };
}

// Zod schemas for runtime validation
export const ZodSchemas = {
  // Common types
  Email: z.string().email(),
  Username: z
    .string()
    .min(3)
    .max(30)
    .regex(/^[a-zA-Z0-9_]+$/),
  Password: z.string().min(8),
  Slug: z.string().regex(/^[a-z0-9-]+$/),
  URL: z.string().url(),
  UUID: z.string().uuid(),

  // User validation
  UserRole: z.enum([
    "admin",
    "moderator",
    "editor",
    "author",
    "subscriber",
    "guest",
  ]),
  UserStatus: z.enum(["active", "inactive", "pending", "suspended", "banned"]),

  LoginRequest: z.object({
    email: z.string().email(),
    password: z.string().min(8),
    remember_me: z.boolean().optional(),
    mfa_code: z
      .string()
      .regex(/^[0-9]{6}$/)
      .optional(),
  }),

  RegisterRequest: z
    .object({
      username: z
        .string()
        .min(3)
        .max(30)
        .regex(/^[a-zA-Z0-9_]+$/),
      email: z.string().email(),
      password: z.string().min(8),
      password_confirm: z.string().min(8),
      first_name: z.string().max(30).optional(),
      last_name: z.string().max(30).optional(),
      terms_accepted: z.literal(true),
      newsletter_opt_in: z.boolean().optional(),
    })
    .refine((data) => data.password === data.password_confirm, {
      message: "Passwords don't match",
      path: ["password_confirm"],
    }),

  // Blog validation
  PostStatus: z.enum([
    "draft",
    "published",
    "scheduled",
    "archived",
    "deleted",
  ]),
  ContentFormat: z.enum(["markdown", "html", "rich_text", "plain_text"]),
  Visibility: z.enum(["public", "private", "restricted", "draft"]),

  PostCreateRequest: z.object({
    title: z.string().min(1).max(200),
    slug: z
      .string()
      .regex(/^[a-z0-9-]+$/)
      .optional(),
    excerpt: z.string().max(500).optional(),
    content: z.string().min(1),
    content_format: z
      .enum(["markdown", "html", "rich_text", "plain_text"])
      .default("markdown"),
    featured_image_alt: z.string().max(200).optional(),
    category_id: z.number().min(1).optional(),
    tag_ids: z.array(z.number().min(1)).optional(),
    status: z.enum(["draft", "published", "scheduled"]).default("draft"),
    visibility: z
      .enum(["public", "private", "restricted", "draft"])
      .default("public"),
    is_featured: z.boolean().default(false),
    allow_comments: z.boolean().default(true),
    published_at: z.string().datetime().optional(),
    scheduled_at: z.string().datetime().optional(),
  }),

  CategoryCreateRequest: z.object({
    name: z.string().min(1).max(100),
    slug: z
      .string()
      .regex(/^[a-z0-9-]+$/)
      .optional(),
    description: z.string().max(500).optional(),
    color: z
      .string()
      .regex(/^#[0-9A-Fa-f]{6}$/)
      .optional(),
    icon: z.string().max(50).optional(),
    parent_id: z.number().min(1).optional(),
    is_featured: z.boolean().default(false),
    sort_order: z.number().min(0).default(0),
  }),

  TagCreateRequest: z.object({
    name: z.string().min(1).max(50),
    slug: z
      .string()
      .regex(/^[a-z0-9-]+$/)
      .optional(),
    description: z.string().max(200).optional(),
    color: z
      .string()
      .regex(/^#[0-9A-Fa-f]{6}$/)
      .optional(),
  }),

  // Newsletter validation
  SubscriptionStatus: z.enum([
    "active",
    "inactive",
    "pending",
    "unsubscribed",
    "bounced",
    "complained",
  ]),

  SubscriptionRequest: z.object({
    email: z.string().email(),
    first_name: z.string().max(50).optional(),
    last_name: z.string().max(50).optional(),
    tags: z.array(z.string()).optional(),
    source: z.string().max(100).optional(),
    double_opt_in: z.boolean().default(true),
  }),

  // Search validation
  SearchRequest: z.object({
    query: z.string().min(1).max(200),
    page: z.number().min(1).default(1),
    per_page: z.number().min(1).max(100).default(20),
    sort: z
      .array(
        z.object({
          field: z.string(),
          order: z.enum(["asc", "desc"]),
        })
      )
      .optional(),
    filters: z.record(z.unknown()).optional(),
    highlight: z.boolean().default(false),
    facets: z.array(z.string()).optional(),
  }),

  // Pagination validation
  PaginationParams: z.object({
    page: z.number().min(1).default(1),
    per_page: z.number().min(1).max(100).default(20),
  }),

  // Bulk operations validation
  BulkOperationRequest: z.object({
    operation: z.enum(["create", "update", "delete"]),
    items: z.array(z.unknown()).min(1).max(1000),
    options: z
      .object({
        batch_size: z.number().min(1).max(100).default(50),
        continue_on_error: z.boolean().default(false),
      })
      .optional(),
  }),
};

// Validation middleware for Express/Fastify
export function createValidationMiddleware<T extends z.ZodType>(schema: T) {
  return (data: unknown) => {
    try {
      const result = schema.parse(data);
      return { success: true, data: result };
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = error.errors.map((err) => ({
          field: err.path.join("."),
          message: err.message,
          code: err.code,
        }));
        return { success: false, errors };
      }
      return {
        success: false,
        errors: [
          {
            field: "unknown",
            message: "Validation failed",
            code: "VALIDATION_ERROR",
          },
        ],
      };
    }
  };
}

// Utility functions for common validations
export const ValidationUtils = {
  isEmail: (value: string): boolean => {
    return ZodSchemas.Email.safeParse(value).success;
  },

  isUsername: (value: string): boolean => {
    return ZodSchemas.Username.safeParse(value).success;
  },

  isPassword: (value: string): boolean => {
    return ZodSchemas.Password.safeParse(value).success;
  },

  isSlug: (value: string): boolean => {
    return ZodSchemas.Slug.safeParse(value).success;
  },

  isURL: (value: string): boolean => {
    return ZodSchemas.URL.safeParse(value).success;
  },

  isUUID: (value: string): boolean => {
    return ZodSchemas.UUID.safeParse(value).success;
  },

  // Generate slug from title
  generateSlug: (title: string): string => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .trim()
      .replace(/^-+|-+$/g, "");
  },

  // Validate password strength
  validatePasswordStrength: (
    password: string
  ): {
    score: number;
    feedback: string[];
  } => {
    const feedback: string[] = [];
    let score = 0;

    if (password.length >= 8) score += 1;
    else feedback.push("Password should be at least 8 characters long");

    if (/[a-z]/.test(password)) score += 1;
    else feedback.push("Password should contain lowercase letters");

    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push("Password should contain uppercase letters");

    if (/[0-9]/.test(password)) score += 1;
    else feedback.push("Password should contain numbers");

    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    else feedback.push("Password should contain special characters");

    return { score, feedback };
  },

  // Sanitize HTML content
  sanitizeHTML: (html: string): string => {
    // Basic HTML sanitization - in production, use a library like DOMPurify
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, "")
      .replace(/javascript:/gi, "")
      .replace(/on\w+\s*=/gi, "");
  },

  // Validate file upload
  validateFileUpload: (
    file: File,
    options: {
      maxSize?: number;
      allowedTypes?: string[];
      allowedExtensions?: string[];
    } = {}
  ): ValidationResult => {
    const {
      maxSize = 10 * 1024 * 1024, // 10MB default
      allowedTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"],
      allowedExtensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    } = options;

    const errors: Array<{ field: string; message: string; code: string }> = [];

    if (file.size > maxSize) {
      errors.push({
        field: "file",
        message: `File size must be less than ${maxSize / 1024 / 1024}MB`,
        code: "FILE_TOO_LARGE",
      });
    }

    if (!allowedTypes.includes(file.type)) {
      errors.push({
        field: "file",
        message: `File type ${file.type} is not allowed`,
        code: "INVALID_FILE_TYPE",
      });
    }

    const extension = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      errors.push({
        field: "file",
        message: `File extension ${extension} is not allowed`,
        code: "INVALID_FILE_EXTENSION",
      });
    }

    return {
      success: errors.length === 0,
      data: errors.length === 0 ? file : undefined,
      errors: errors.length > 0 ? errors : undefined,
    };
  },
};
