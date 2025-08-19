/**
 * Logging interceptors for request/response monitoring and debugging
 */

import { AxiosRequestConfig, AxiosResponse, AxiosError } from "axios";

export interface LoggingInterceptorConfig {
  enableRequestLogging?: boolean;
  enableResponseLogging?: boolean;
  enableErrorLogging?: boolean;
  logLevel?: "error" | "warn" | "info" | "debug";
  logHeaders?: boolean;
  logBody?: boolean;
  maxBodyLength?: number;
  sensitiveHeaders?: string[];
  onLog?: (logData: LogData) => void;
}

export interface LogData {
  type: "request" | "response" | "error";
  method?: string;
  url?: string;
  status?: number;
  duration?: number;
  headers?: Record<string, any>;
  body?: any;
  error?: any;
  timestamp: string;
}

export class LoggingInterceptor {
  private config: Required<LoggingInterceptorConfig>;

  constructor(config: LoggingInterceptorConfig = {}) {
    this.config = {
      enableRequestLogging: true,
      enableResponseLogging: true,
      enableErrorLogging: true,
      logLevel: "debug",
      logHeaders: false,
      logBody: false,
      maxBodyLength: 1000,
      sensitiveHeaders: ["authorization", "cookie", "x-api-key"],
      onLog: undefined,
      ...config,
    };
  }

  /**
   * Request interceptor for logging outgoing requests
   */
  onRequest = (config: AxiosRequestConfig): AxiosRequestConfig => {
    if (!this.config.enableRequestLogging) {
      return config;
    }

    // Add start time for duration calculation
    config.metadata = {
      ...config.metadata,
      startTime: Date.now(),
    };

    const logData: LogData = {
      type: "request",
      method: config.method?.toUpperCase(),
      url: this.buildFullUrl(config),
      headers: this.config.logHeaders
        ? this.sanitizeHeaders(config.headers)
        : undefined,
      body: this.config.logBody ? this.sanitizeBody(config.data) : undefined,
      timestamp: new Date().toISOString(),
    };

    this.log(logData);
    return config;
  };

  /**
   * Request error interceptor
   */
  onRequestError = (error: any): Promise<any> => {
    if (this.config.enableErrorLogging) {
      const logData: LogData = {
        type: "error",
        error: error.message || "Request setup failed",
        timestamp: new Date().toISOString(),
      };

      this.log(logData);
    }

    return Promise.reject(error);
  };

  /**
   * Response interceptor for logging successful responses
   */
  onResponse = (response: AxiosResponse): AxiosResponse => {
    if (!this.config.enableResponseLogging) {
      return response;
    }

    const duration = this.calculateDuration(response.config);

    const logData: LogData = {
      type: "response",
      method: response.config.method?.toUpperCase(),
      url: this.buildFullUrl(response.config),
      status: response.status,
      duration,
      headers: this.config.logHeaders
        ? this.sanitizeHeaders(response.headers)
        : undefined,
      body: this.config.logBody ? this.sanitizeBody(response.data) : undefined,
      timestamp: new Date().toISOString(),
    };

    this.log(logData);
    return response;
  };

  /**
   * Response error interceptor for logging failed responses
   */
  onResponseError = (error: AxiosError): Promise<any> => {
    if (!this.config.enableErrorLogging) {
      return Promise.reject(error);
    }

    const duration = error.config
      ? this.calculateDuration(error.config)
      : undefined;

    const logData: LogData = {
      type: "error",
      method: error.config?.method?.toUpperCase(),
      url: error.config ? this.buildFullUrl(error.config) : undefined,
      status: error.response?.status,
      duration,
      headers:
        this.config.logHeaders && error.response?.headers
          ? this.sanitizeHeaders(error.response.headers)
          : undefined,
      body:
        this.config.logBody && error.response?.data
          ? this.sanitizeBody(error.response.data)
          : undefined,
      error: error.message,
      timestamp: new Date().toISOString(),
    };

    this.log(logData);
    return Promise.reject(error);
  };

  /**
   * Calculate request duration
   */
  private calculateDuration(config: AxiosRequestConfig): number | undefined {
    const startTime = config.metadata?.startTime;
    return startTime ? Date.now() - startTime : undefined;
  }

  /**
   * Build full URL from config
   */
  private buildFullUrl(config: AxiosRequestConfig): string {
    const baseURL = config.baseURL || "";
    const url = config.url || "";
    return baseURL + url;
  }

  /**
   * Sanitize headers by removing sensitive information
   */
  private sanitizeHeaders(headers: any): Record<string, any> {
    if (!headers) return {};

    const sanitized: Record<string, any> = {};

    Object.keys(headers).forEach((key) => {
      const lowerKey = key.toLowerCase();
      if (this.config.sensitiveHeaders.includes(lowerKey)) {
        sanitized[key] = "[REDACTED]";
      } else {
        sanitized[key] = headers[key];
      }
    });

    return sanitized;
  }

  /**
   * Sanitize request/response body
   */
  private sanitizeBody(body: any): any {
    if (!body) return undefined;

    try {
      let bodyString: string;

      if (typeof body === "string") {
        bodyString = body;
      } else {
        bodyString = JSON.stringify(body);
      }

      // Truncate if too long
      if (bodyString.length > this.config.maxBodyLength) {
        return (
          bodyString.substring(0, this.config.maxBodyLength) + "... [TRUNCATED]"
        );
      }

      return body;
    } catch (error) {
      return "[UNPARSEABLE BODY]";
    }
  }

  /**
   * Log data using appropriate method
   */
  private log(logData: LogData): void {
    // Call custom log handler if provided
    if (this.config.onLog) {
      this.config.onLog(logData);
      return;
    }

    // Use console logging
    const message = this.formatLogMessage(logData);

    switch (this.config.logLevel) {
      case "error":
        if (logData.type === "error") {
          console.error(message, logData);
        }
        break;
      case "warn":
        if (logData.type === "error") {
          console.warn(message, logData);
        }
        break;
      case "info":
        if (logData.type === "error") {
          console.info(message, logData);
        } else if (logData.status && logData.status >= 400) {
          console.info(message, logData);
        }
        break;
      case "debug":
        console.debug(message, logData);
        break;
    }
  }

  /**
   * Format log message for console output
   */
  private formatLogMessage(logData: LogData): string {
    const { type, method, url, status, duration } = logData;

    let message = `[API ${type.toUpperCase()}]`;

    if (method && url) {
      message += ` ${method} ${url}`;
    }

    if (status) {
      message += ` ${status}`;
    }

    if (duration !== undefined) {
      message += ` (${duration}ms)`;
    }

    if (type === "error" && logData.error) {
      message += ` - ${logData.error}`;
    }

    return message;
  }
}
