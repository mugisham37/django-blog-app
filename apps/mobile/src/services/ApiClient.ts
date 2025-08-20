import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import {API_CONFIG, STORAGE_KEYS, ERROR_MESSAGES} from '@config/constants';
import {OfflineManager} from '@services/OfflineManager';
import {HTTPClient, ClientConfig} from '@fullstack-monolith/api-client';
import type {APIResponse, AuthTokens} from '@fullstack-monolith/api-client';

class ApiClientClass {
  private instance: AxiosInstance;
  private httpClient: HTTPClient;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }> = [];

  constructor() {
    // Initialize the shared HTTP client
    const clientConfig: ClientConfig = {
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      retries: 3,
      retryDelay: 1000,
      enableCache: true,
      defaultCacheTTL: 300000, // 5 minutes
    };

    this.httpClient = new HTTPClient(clientConfig);

    // Keep the legacy axios instance for backward compatibility
    this.instance = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
    this.initializeTokens();
  }

  private async initializeTokens() {
    try {
      const accessToken = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      const expiresAt = await AsyncStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES_AT);

      if (accessToken && refreshToken) {
        const tokens: AuthTokens = {
          access: accessToken,
          refresh: refreshToken,
          expires_at: expiresAt || undefined,
        };
        this.httpClient.setTokens(tokens);
      }
    } catch (error) {
      console.error('Failed to initialize tokens:', error);
    }
  }

  public async setTokens(tokens: AuthTokens) {
    try {
      await Promise.all([
        AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access),
        AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh),
        tokens.expires_at ? AsyncStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES_AT, tokens.expires_at) : Promise.resolve(),
      ]);
      this.httpClient.setTokens(tokens);
    } catch (error) {
      console.error('Failed to set tokens:', error);
    }
  }

  public async clearTokens() {
    try {
      await Promise.all([
        AsyncStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN),
        AsyncStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
        AsyncStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRES_AT),
        AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA),
      ]);
      this.httpClient.clearTokens();
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  }

  public getTokens(): AuthTokens | null {
    return this.httpClient.getTokens();
  }

  // Initialize method for app startup
  public static async initialize() {
    // Any initialization logic needed for the API client
    console.log('API Client initialized');
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      async (config) => {
        // Check network connectivity
        const netInfo = await NetInfo.fetch();
        if (!netInfo.isConnected) {
          // Store request for offline processing
          await OfflineManager.storeOfflineRequest(config);
          throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
        }

        // Add auth token if available
        const token = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
        if (token && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If already refreshing, queue the request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({resolve, reject});
            }).then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.instance(originalRequest);
            }).catch((err) => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
            if (!refreshToken) {
              throw new Error('No refresh token available');
            }

            const response = await this.instance.post('/auth/refresh/', {
              refresh_token: refreshToken,
            });

            const {access_token, refresh_token} = response.data;

            await Promise.all([
              AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access_token),
              AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh_token),
            ]);

            // Process failed queue
            this.processQueue(null, access_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.instance(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError, null);
            
            // Clear stored tokens
            await Promise.all([
              AsyncStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN),
              AsyncStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
              AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA),
            ]);

            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Handle network errors
        if (!error.response) {
          // Store request for offline retry
          await OfflineManager.storeOfflineRequest(originalRequest);
          error.message = ERROR_MESSAGES.NETWORK_ERROR;
        }

        // Handle timeout errors
        if (error.code === 'ECONNABORTED') {
          error.message = ERROR_MESSAGES.TIMEOUT_ERROR;
        }

        // Handle server errors
        if (error.response?.status >= 500) {
          error.message = ERROR_MESSAGES.SERVER_ERROR;
        }

        return Promise.reject(error);
      }
    );
  }

  private processQueue(error: any, token: string | null) {
    this.failedQueue.forEach(({resolve, reject}) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });

    this.failedQueue = [];
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Enhanced HTTP Methods using shared client
  async get<T = any>(url: string, params?: any, config?: {cache?: boolean; cacheTTL?: number}): Promise<APIResponse<T>> {
    try {
      // Check network connectivity for mobile
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        // Try to get from offline storage
        const offlineData = await OfflineManager.getOfflineData(url);
        if (offlineData) {
          return offlineData;
        }
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }

      return await this.httpClient.get<T>(url, params, config);
    } catch (error) {
      console.error('GET request failed:', error);
      throw error;
    }
  }

  async post<T = any>(url: string, data?: any, config?: {cache?: boolean}): Promise<APIResponse<T>> {
    try {
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        // Store for offline processing
        await OfflineManager.storeOfflineRequest({
          method: 'POST',
          url,
          data,
        });
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }

      return await this.httpClient.post<T>(url, data, config);
    } catch (error) {
      console.error('POST request failed:', error);
      throw error;
    }
  }

  async put<T = any>(url: string, data?: any, config?: {cache?: boolean}): Promise<APIResponse<T>> {
    try {
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        await OfflineManager.storeOfflineRequest({
          method: 'PUT',
          url,
          data,
        });
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }

      return await this.httpClient.put<T>(url, data, config);
    } catch (error) {
      console.error('PUT request failed:', error);
      throw error;
    }
  }

  async patch<T = any>(url: string, data?: any, config?: {cache?: boolean}): Promise<APIResponse<T>> {
    try {
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        await OfflineManager.storeOfflineRequest({
          method: 'PATCH',
          url,
          data,
        });
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }

      return await this.httpClient.patch<T>(url, data, config);
    } catch (error) {
      console.error('PATCH request failed:', error);
      throw error;
    }
  }

  async delete<T = any>(url: string, config?: {cache?: boolean}): Promise<APIResponse<T>> {
    try {
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        await OfflineManager.storeOfflineRequest({
          method: 'DELETE',
          url,
        });
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }

      return await this.httpClient.delete<T>(url, config);
    } catch (error) {
      console.error('DELETE request failed:', error);
      throw error;
    }
  }

  // Legacy HTTP Methods for backward compatibility
  async getLegacy<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get(url, config);
  }

  async postLegacy<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.post(url, data, config);
  }

  async putLegacy<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.put(url, data, config);
  }

  async patchLegacy<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.patch(url, data, config);
  }

  async deleteLegacy<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete(url, config);
  }

  // Upload file with progress
  async uploadFile<T = any>(
    url: string,
    file: FormData,
    onUploadProgress?: (progressEvent: any) => void,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.post(url, file, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  }

  // Download file with progress
  async downloadFile(
    url: string,
    onDownloadProgress?: (progressEvent: any) => void,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<Blob>> {
    return this.instance.get(url, {
      ...config,
      responseType: 'blob',
      onDownloadProgress,
    });
  }

  // Cancel request
  cancelRequest(source: any) {
    source.cancel('Request canceled by user');
  }

  // Create cancel token
  createCancelToken() {
    return axios.CancelToken.source();
  }

  // Set base URL
  setBaseURL(baseURL: string) {
    this.instance.defaults.baseURL = baseURL;
  }

  // Set default headers
  setDefaultHeaders(headers: Record<string, string>) {
    Object.assign(this.instance.defaults.headers, headers);
  }

  // Get instance for advanced usage
  getInstance(): AxiosInstance {
    return this.instance;
  }
}

export const ApiClient = new ApiClientClass();