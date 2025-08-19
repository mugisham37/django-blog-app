/**
 * API-related type definitions
 */

import { PaginationMeta, HttpMethod } from "./common";

// Generic API response wrapper
export interface APIResponse<T = unknown> {
  readonly success: boolean;
  readonly data: T;
  readonly message: string;
  readonly errors?: Record<string, string[]>;
  readonly meta?: Record<string, unknown>;
}

// Paginated API response
export interface PaginatedResponse<T = unknown> extends APIResponse<T[]> {
  readonly pagination: PaginationMeta;
}

// API error response
export interface APIError {
  readonly success: false;
  readonly message: string;
  readonly errors: Record<string, string[]>;
  readonly code?: string;
  readonly status?: number;
  readonly timestamp?: string;
}

// API request configuration
export interface APIRequestConfig {
  readonly method: HttpMethod;
  readonly url: string;
  readonly headers?: Record<string, string>;
  readonly params?: Record<string, unknown>;
  readonly data?: unknown;
  readonly timeout?: number;
  readonly retries?: number;
}

// API client configuration
export interface APIClientConfig {
  readonly baseURL: string;
  readonly timeout: number;
  readonly retries: number;
  readonly headers: Record<string, string>;
  readonly interceptors?: {
    readonly request?: Array<(config: APIRequestConfig) => APIRequestConfig>;
    readonly response?: Array<(response: APIResponse) => APIResponse>;
  };
}

// Authentication token response
export interface TokenResponse {
  readonly access_token: string;
  readonly refresh_token: string;
  readonly token_type: "Bearer";
  readonly expires_in: number;
  readonly scope?: string;
}

// Token refresh request
export interface TokenRefreshRequest {
  readonly refresh_token: string;
}

// API versioning
export type APIVersion = "v1" | "v2";

// API endpoint paths
export interface APIEndpoints {
  readonly auth: {
    readonly login: string;
    readonly logout: string;
    readonly refresh: string;
    readonly register: string;
    readonly resetPassword: string;
    readonly changePassword: string;
    readonly profile: string;
  };
  readonly blog: {
    readonly posts: string;
    readonly post: (id: number) => string;
    readonly categories: string;
    readonly category: (id: number) => string;
    readonly tags: string;
    readonly tag: (id: number) => string;
  };
  readonly comments: {
    readonly comments: string;
    readonly comment: (id: number) => string;
    readonly postComments: (postId: number) => string;
  };
  readonly analytics: {
    readonly pageViews: string;
    readonly searchQueries: string;
    readonly userActivity: string;
  };
  readonly newsletter: {
    readonly subscribe: string;
    readonly unsubscribe: string;
    readonly campaigns: string;
    readonly campaign: (id: number) => string;
  };
}

// HTTP status codes
export enum HTTPStatus {
  OK = 200,
  CREATED = 201,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  METHOD_NOT_ALLOWED = 405,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  TOO_MANY_REQUESTS = 429,
  INTERNAL_SERVER_ERROR = 500,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
  GATEWAY_TIMEOUT = 504,
}

// Rate limiting information
export interface RateLimitInfo {
  readonly limit: number;
  readonly remaining: number;
  readonly reset: number;
  readonly retry_after?: number;
}

// API health check response
export interface HealthCheckResponse {
  readonly status: "healthy" | "unhealthy" | "degraded";
  readonly checks: Record<string, boolean>;
  readonly timestamp: string;
  readonly version: string;
  readonly uptime: number;
}

// Bulk operation request
export interface BulkOperationRequest<T = unknown> {
  readonly operation: "create" | "update" | "delete";
  readonly items: T[];
  readonly options?: {
    readonly batch_size?: number;
    readonly continue_on_error?: boolean;
  };
}

// Bulk operation response
export interface BulkOperationResponse<T = unknown> {
  readonly success: boolean;
  readonly processed: number;
  readonly failed: number;
  readonly results: Array<{
    readonly item: T;
    readonly success: boolean;
    readonly error?: string;
  }>;
}

// Search request
export interface SearchRequest {
  readonly query: string;
  readonly filters?: Record<string, unknown>;
  readonly sort?: Array<{
    readonly field: string;
    readonly order: "asc" | "desc";
  }>;
  readonly page?: number;
  readonly per_page?: number;
  readonly highlight?: boolean;
  readonly facets?: string[];
}

// Search response
export interface SearchResponse<T = unknown> {
  readonly results: T[];
  readonly total: number;
  readonly took: number;
  readonly facets?: Record<
    string,
    Array<{
      readonly value: string;
      readonly count: number;
    }>
  >;
  readonly highlights?: Record<string, string[]>;
}

// Export/import request
export interface ExportRequest {
  readonly format: "json" | "csv" | "xlsx" | "pdf";
  readonly filters?: Record<string, unknown>;
  readonly fields?: string[];
  readonly options?: Record<string, unknown>;
}

// Export response
export interface ExportResponse {
  readonly file_url: string;
  readonly file_name: string;
  readonly file_size: number;
  readonly expires_at: string;
  readonly format: string;
}

// Import request
export interface ImportRequest {
  readonly file_url: string;
  readonly format: "json" | "csv" | "xlsx";
  readonly options?: {
    readonly skip_header?: boolean;
    readonly batch_size?: number;
    readonly update_existing?: boolean;
  };
}

// Import response
export interface ImportResponse {
  readonly job_id: string;
  readonly status: "pending" | "processing" | "completed" | "failed";
  readonly processed: number;
  readonly total: number;
  readonly errors?: string[];
}
