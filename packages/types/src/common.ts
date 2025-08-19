/**
 * Common types used across the application
 */

// Base entity interface
export interface BaseEntity {
  readonly id: number;
  readonly created_at: string;
  readonly updated_at: string;
}

// Timestamp interface for entities with timestamps
export interface Timestamps {
  readonly created_at: string;
  readonly updated_at: string;
}

// Soft delete interface
export interface SoftDelete {
  readonly deleted_at: string | null;
  readonly is_deleted: boolean;
}

// Pagination metadata
export interface PaginationMeta {
  readonly page: number;
  readonly pages: number;
  readonly per_page: number;
  readonly total: number;
  readonly has_next: boolean;
  readonly has_prev: boolean;
}

// Sort order
export type SortOrder = "asc" | "desc";

// Generic sort interface
export interface Sort {
  readonly field: string;
  readonly order: SortOrder;
}

// Filter operators
export type FilterOperator =
  | "eq"
  | "ne"
  | "gt"
  | "gte"
  | "lt"
  | "lte"
  | "in"
  | "nin"
  | "contains"
  | "icontains"
  | "startswith"
  | "endswith"
  | "isnull";

// Generic filter interface
export interface Filter {
  readonly field: string;
  readonly operator: FilterOperator;
  readonly value: unknown;
}

// Search parameters
export interface SearchParams {
  readonly q?: string;
  readonly page?: number;
  readonly per_page?: number;
  readonly sort?: Sort[];
  readonly filters?: Filter[];
}

// File upload interface
export interface FileUpload {
  readonly file: File;
  readonly name: string;
  readonly size: number;
  readonly type: string;
  readonly url?: string;
}

// Image dimensions
export interface ImageDimensions {
  readonly width: number;
  readonly height: number;
}

// Image upload with dimensions
export interface ImageUpload extends FileUpload {
  readonly dimensions?: ImageDimensions;
  readonly alt_text?: string;
}

// Status types
export type Status =
  | "active"
  | "inactive"
  | "pending"
  | "suspended"
  | "deleted";

// Priority levels
export type Priority = "low" | "medium" | "high" | "critical";

// Visibility levels
export type Visibility = "public" | "private" | "restricted" | "draft";

// Language codes (ISO 639-1)
export type LanguageCode =
  | "en"
  | "es"
  | "fr"
  | "de"
  | "it"
  | "pt"
  | "ru"
  | "zh"
  | "ja"
  | "ko";

// Currency codes (ISO 4217)
export type CurrencyCode =
  | "USD"
  | "EUR"
  | "GBP"
  | "JPY"
  | "CAD"
  | "AUD"
  | "CHF"
  | "CNY";

// Country codes (ISO 3166-1 alpha-2)
export type CountryCode =
  | "US"
  | "CA"
  | "GB"
  | "DE"
  | "FR"
  | "IT"
  | "ES"
  | "JP"
  | "AU"
  | "BR";

// Timezone identifiers
export type TimezoneId =
  | "UTC"
  | "America/New_York"
  | "America/Chicago"
  | "America/Denver"
  | "America/Los_Angeles"
  | "Europe/London"
  | "Europe/Paris"
  | "Europe/Berlin"
  | "Asia/Tokyo"
  | "Asia/Shanghai"
  | "Australia/Sydney";

// Environment types
export type Environment = "development" | "staging" | "production" | "test";

// Log levels
export type LogLevel = "debug" | "info" | "warn" | "error" | "fatal";

// HTTP methods
export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "HEAD"
  | "OPTIONS";

// Content types
export type ContentType =
  | "application/json"
  | "application/xml"
  | "text/html"
  | "text/plain"
  | "multipart/form-data"
  | "application/x-www-form-urlencoded";

// Generic key-value pairs
export interface KeyValuePair<T = string> {
  readonly key: string;
  readonly value: T;
}

// Generic dictionary
export type Dictionary<T = unknown> = Record<string, T>;

// Generic nullable type
export type Nullable<T> = T | null;

// Generic optional type
export type Optional<T> = T | undefined;

// Generic array or single item
export type ArrayOrSingle<T> = T | T[];

// Utility type for making all properties optional
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Utility type for making specific properties required
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Utility type for deep readonly
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

// Utility type for deep partial
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
