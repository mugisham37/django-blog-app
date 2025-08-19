/**
 * HTTP client with request/response interceptors and automatic token refresh
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from "axios";
import axiosRetry from "axios-retry";
import qs from "qs";
import {
  APIResponse,
  APIError,
  AuthTokens,
  RefreshTokenResponse,
  RequestConfig,
} from "./types";

export interface ClientConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  enableCache?: boolean;
  defaultCacheTTL?: number;
}

export class HTTPClient {
  private axios: AxiosInstance;
  private tokens: AuthTokens | null = null;
  private refreshPromise: Promise<string> | null = null;
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> =
    new Map();
  private config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = {
      timeout: 10000,
      retries: 3,
      retryDelay: 1000,
      enableCache: true,
      defaultCacheTTL: 300000, // 5 minutes
      ...config,
    };

    this.axios = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      paramsSerializer: (params) =>
        qs.stringify(params, { arrayFormat: "brackets" }),
    });

    this.setupInterceptors();
    this.setupRetry();
    this.loadTokensFromStorage();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.axios.interceptors.request.use(
      (config) => {
        // Add authentication token
        if (this.tokens?.access) {
          config.headers.Authorization = `Bearer ${this.tokens.access}`;
        }

        // Add common headers
        config.headers["Content-Type"] =
          config.headers["Content-Type"] || "application/json";
        config.headers["Accept"] = "application/json";

        // Add request timestamp for debugging
        config.metadata = { startTime: Date.now() };

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.axios.interceptors.response.use(
      (response) => {
        // Log response time for debugging
        const endTime = Date.now();
        const startTime = response.config.metadata?.startTime || endTime;
        console.debug(
          `API Request to ${response.config.url} took ${endTime - startTime}ms`
        );

        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & {
          _retry?: boolean;
        };

        // Handle token refresh for 401 errors
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          this.tokens?.refresh
        ) {
          originalRequest._retry = true;

          try {
            const newAccessToken = await this.refreshAccessToken();
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return this.axios(originalRequest);
          } catch (refreshError) {
            this.clearTokens();
            throw this.createAPIError(error);
          }
        }

        throw this.createAPIError(error);
      }
    );
  }

  private setupRetry(): void {
    axiosRetry(this.axios, {
      retries: this.config.retries || 3,
      retryDelay: (retryCount) => {
        return retryCount * (this.config.retryDelay || 1000);
      },
      retryCondition: (error) => {
        // Retry on network errors and 5xx status codes
        return (
          axiosRetry.isNetworkOrIdempotentRequestError(error) ||
          (error.response?.status ? error.response.status >= 500 : false)
        );
      },
    });
  }

  private createAPIError(error: AxiosError): APIError {
    const response = error.response;
    const data = response?.data as any;

    return {
      message: data?.message || error.message || "An unexpected error occurred",
      code: data?.code || error.code || "UNKNOWN_ERROR",
      details: data?.errors || data?.details || {},
      status: response?.status,
    };
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.tokens?.refresh) {
      throw new Error("No refresh token available");
    }

    this.refreshPromise = this.performTokenRefresh();

    try {
      const newAccessToken = await this.refreshPromise;
      return newAccessToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    try {
      const response = await axios.post<RefreshTokenResponse>(
        `${this.config.baseURL}/auth/token/refresh/`,
        { refresh: this.tokens!.refresh }
      );

      const { access, expires_at } = response.data;

      this.tokens = {
        ...this.tokens!,
        access,
        expires_at,
      };

      this.saveTokensToStorage();
      return access;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  private getCacheKey(method: string, url: string, params?: any): string {
    return `${method}:${url}:${JSON.stringify(params || {})}`;
  }

  private getFromCache<T>(key: string): T | null {
    if (!this.config.enableCache) return null;

    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  private setCache<T>(key: string, data: T, ttl?: number): void {
    if (!this.config.enableCache) return;

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultCacheTTL || 300000,
    });
  }

  private clearCache(): void {
    this.cache.clear();
  }

  public setTokens(tokens: AuthTokens): void {
    this.tokens = tokens;
    this.saveTokensToStorage();
  }

  public clearTokens(): void {
    this.tokens = null;
    this.removeTokensFromStorage();
    this.clearCache();
  }

  public getTokens(): AuthTokens | null {
    return this.tokens;
  }

  private saveTokensToStorage(): void {
    if (typeof window !== "undefined" && this.tokens) {
      localStorage.setItem("auth_tokens", JSON.stringify(this.tokens));
    }
  }

  private loadTokensFromStorage(): void {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth_tokens");
      if (stored) {
        try {
          this.tokens = JSON.parse(stored);
        } catch (error) {
          console.warn("Failed to parse stored tokens:", error);
          this.removeTokensFromStorage();
        }
      }
    }
  }

  private removeTokensFromStorage(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_tokens");
    }
  }

  public async get<T>(
    url: string,
    params?: any,
    config?: RequestConfig
  ): Promise<APIResponse<T>> {
    const cacheKey = this.getCacheKey("GET", url, params);

    if (config?.cache !== false) {
      const cached = this.getFromCache<APIResponse<T>>(cacheKey);
      if (cached) return cached;
    }

    const response = await this.axios.get<APIResponse<T>>(url, { params });

    if (config?.cache !== false) {
      this.setCache(cacheKey, response.data, config?.cacheTTL);
    }

    return response.data;
  }

  public async post<T>(
    url: string,
    data?: any,
    config?: RequestConfig
  ): Promise<APIResponse<T>> {
    const response = await this.axios.post<APIResponse<T>>(url, data);
    this.clearCache(); // Clear cache on mutations
    return response.data;
  }

  public async put<T>(
    url: string,
    data?: any,
    config?: RequestConfig
  ): Promise<APIResponse<T>> {
    const response = await this.axios.put<APIResponse<T>>(url, data);
    this.clearCache(); // Clear cache on mutations
    return response.data;
  }

  public async patch<T>(
    url: string,
    data?: any,
    config?: RequestConfig
  ): Promise<APIResponse<T>> {
    const response = await this.axios.patch<APIResponse<T>>(url, data);
    this.clearCache(); // Clear cache on mutations
    return response.data;
  }

  public async delete<T>(
    url: string,
    config?: RequestConfig
  ): Promise<APIResponse<T>> {
    const response = await this.axios.delete<APIResponse<T>>(url);
    this.clearCache(); // Clear cache on mutations
    return response.data;
  }

  public async upload<T>(
    url: string,
    file: File,
    data?: any,
    onProgress?: (progress: number) => void
  ): Promise<APIResponse<T>> {
    const formData = new FormData();
    formData.append("file", file);

    if (data) {
      Object.keys(data).forEach((key) => {
        formData.append(key, data[key]);
      });
    }

    const response = await this.axios.post<APIResponse<T>>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });

    this.clearCache(); // Clear cache on mutations
    return response.data;
  }
}
