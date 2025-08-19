/**
 * Main entry point for the API client package
 */

// Export main API client
export { APIClient } from "./api-client";

// Export HTTP client for advanced usage
export { HTTPClient } from "./client";
export type { ClientConfig } from "./client";

// Export all services
export * from "./services";

// Export all types
export * from "./types";

// Export interceptors for custom usage
export * from "./interceptors";

// Default export
export { APIClient as default } from "./api-client";
