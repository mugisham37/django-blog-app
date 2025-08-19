/**
 * Authentication interceptors for automatic token handling
 */

import { AxiosRequestConfig, AxiosResponse, AxiosError } from "axios";
import { AuthTokens } from "../types";

export interface AuthInterceptorConfig {
  getTokens: () => AuthTokens | null;
  setTokens: (tokens: AuthTokens) => void;
  clearTokens: () => void;
  refreshTokenEndpoint: string;
  onTokenRefreshFailed?: () => void;
}

export class AuthInterceptor {
  private refreshPromise: Promise<string> | null = null;

  constructor(private config: AuthInterceptorConfig) {}

  /**
   * Request interceptor to add authentication token
   */
  onRequest = (config: AxiosRequestConfig): AxiosRequestConfig => {
    const tokens = this.config.getTokens();

    if (tokens?.access) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${tokens.access}`;
    }

    return config;
  };

  /**
   * Request error interceptor
   */
  onRequestError = (error: any): Promise<any> => {
    return Promise.reject(error);
  };

  /**
   * Response interceptor for successful responses
   */
  onResponse = (response: AxiosResponse): AxiosResponse => {
    return response;
  };

  /**
   * Response error interceptor for token refresh
   */
  onResponseError = async (error: AxiosError): Promise<any> => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const tokens = this.config.getTokens();

      if (tokens?.refresh) {
        originalRequest._retry = true;

        try {
          const newAccessToken = await this.refreshAccessToken();
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

          // Retry the original request with new token
          return axios(originalRequest);
        } catch (refreshError) {
          this.config.clearTokens();
          if (this.config.onTokenRefreshFailed) {
            this.config.onTokenRefreshFailed();
          }
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available, clear tokens
        this.config.clearTokens();
        if (this.config.onTokenRefreshFailed) {
          this.config.onTokenRefreshFailed();
        }
      }
    }

    return Promise.reject(error);
  };

  /**
   * Refresh access token using refresh token
   */
  private async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const tokens = this.config.getTokens();
    if (!tokens?.refresh) {
      throw new Error("No refresh token available");
    }

    this.refreshPromise = this.performTokenRefresh(tokens.refresh);

    try {
      const newAccessToken = await this.refreshPromise;
      return newAccessToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  /**
   * Perform the actual token refresh request
   */
  private async performTokenRefresh(refreshToken: string): Promise<string> {
    try {
      const response = await axios.post(this.config.refreshTokenEndpoint, {
        refresh: refreshToken,
      });

      const { access, expires_at } = response.data;
      const currentTokens = this.config.getTokens();

      if (currentTokens) {
        const newTokens = {
          ...currentTokens,
          access,
          expires_at,
        };
        this.config.setTokens(newTokens);
      }

      return access;
    } catch (error) {
      this.config.clearTokens();
      throw error;
    }
  }
}
