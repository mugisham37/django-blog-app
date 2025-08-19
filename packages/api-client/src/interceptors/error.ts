/**
 * Error handling interceptors for consistent error processing
 */

import { AxiosError, AxiosResponse } from "axios";
import { APIError } from "../types";

export interface ErrorInterceptorConfig {
  onError?: (error: APIError) => void;
  enableLogging?: boolean;
  logLevel?: "error" | "warn" | "info" | "debug";
}

export class ErrorInterceptor {
  constructor(private config: ErrorInterceptorConfig = {}) {}

  /**
   * Response interceptor for successful responses
   */
  onResponse = (response: AxiosResponse): AxiosResponse => {
    return response;
  };

  /**
   * Response error interceptor for error handling
   */
  onResponseError = (error: AxiosError): Promise<APIError> => {
    const apiError = this.createAPIError(error);

    // Log error if logging is enabled
    if (this.config.enableLogging) {
      this.logError(apiError, error);
    }

    // Call custom error handler if provided
    if (this.config.onError) {
      this.config.onError(apiError);
    }

    return Promise.reject(apiError);
  };

  /**
   * Create standardized API error from Axios error
   */
  private createAPIError(error: AxiosError): APIError {
    const response = error.response;
    const data = response?.data as any;

    // Extract error information from response
    let message = "An unexpected error occurred";
    let code = "UNKNOWN_ERROR";
    let details = {};

    if (data) {
      // Handle Django REST Framework error format
      if (data.detail) {
        message = data.detail;
      } else if (data.message) {
        message = data.message;
      } else if (data.error) {
        message = data.error;
      } else if (typeof data === "string") {
        message = data;
      }

      // Extract error code
      if (data.code) {
        code = data.code;
      } else if (data.error_code) {
        code = data.error_code;
      }

      // Extract validation errors or additional details
      if (data.errors) {
        details = data.errors;
      } else if (data.non_field_errors) {
        details = { non_field_errors: data.non_field_errors };
      } else if (data.field_errors) {
        details = data.field_errors;
      }
    } else if (error.message) {
      message = error.message;
    }

    // Set code based on HTTP status if not provided
    if (code === "UNKNOWN_ERROR" && response?.status) {
      code = this.getErrorCodeFromStatus(response.status);
    }

    return {
      message,
      code,
      details,
      status: response?.status,
    };
  }

  /**
   * Get error code from HTTP status
   */
  private getErrorCodeFromStatus(status: number): string {
    switch (status) {
      case 400:
        return "BAD_REQUEST";
      case 401:
        return "UNAUTHORIZED";
      case 403:
        return "FORBIDDEN";
      case 404:
        return "NOT_FOUND";
      case 409:
        return "CONFLICT";
      case 422:
        return "VALIDATION_ERROR";
      case 429:
        return "RATE_LIMITED";
      case 500:
        return "INTERNAL_SERVER_ERROR";
      case 502:
        return "BAD_GATEWAY";
      case 503:
        return "SERVICE_UNAVAILABLE";
      case 504:
        return "GATEWAY_TIMEOUT";
      default:
        return "UNKNOWN_ERROR";
    }
  }

  /**
   * Log error with appropriate level
   */
  private logError(apiError: APIError, originalError: AxiosError): void {
    const logLevel = this.config.logLevel || "error";
    const logData = {
      message: apiError.message,
      code: apiError.code,
      status: apiError.status,
      details: apiError.details,
      url: originalError.config?.url,
      method: originalError.config?.method?.toUpperCase(),
      timestamp: new Date().toISOString(),
    };

    switch (logLevel) {
      case "error":
        console.error("API Error:", logData);
        break;
      case "warn":
        console.warn("API Warning:", logData);
        break;
      case "info":
        console.info("API Info:", logData);
        break;
      case "debug":
        console.debug("API Debug:", logData);
        break;
    }
  }
}

/**
 * Utility function to check if error is a specific type
 */
export const isAPIError = (error: any): error is APIError => {
  return (
    error && typeof error === "object" && "message" in error && "code" in error
  );
};

/**
 * Utility function to check if error is a validation error
 */
export const isValidationError = (error: APIError): boolean => {
  return error.code === "VALIDATION_ERROR" || error.status === 422;
};

/**
 * Utility function to check if error is an authentication error
 */
export const isAuthError = (error: APIError): boolean => {
  return error.code === "UNAUTHORIZED" || error.status === 401;
};

/**
 * Utility function to check if error is a permission error
 */
export const isPermissionError = (error: APIError): boolean => {
  return error.code === "FORBIDDEN" || error.status === 403;
};

/**
 * Utility function to check if error is a not found error
 */
export const isNotFoundError = (error: APIError): boolean => {
  return error.code === "NOT_FOUND" || error.status === 404;
};

/**
 * Utility function to check if error is a server error
 */
export const isServerError = (error: APIError): boolean => {
  return error.status ? error.status >= 500 : false;
};
