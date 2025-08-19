/**
 * Main API client class that provides access to all services
 */

import { HTTPClient, ClientConfig } from "./client";
import { AuthService, UserService, BlogService } from "./services";

export class APIClient {
  private httpClient: HTTPClient;

  public readonly auth: AuthService;
  public readonly users: UserService;
  public readonly blog: BlogService;

  constructor(config: ClientConfig) {
    this.httpClient = new HTTPClient(config);

    // Initialize services
    this.auth = new AuthService(this.httpClient);
    this.users = new UserService(this.httpClient);
    this.blog = new BlogService(this.httpClient);
  }

  /**
   * Get the underlying HTTP client for custom requests
   */
  getHTTPClient(): HTTPClient {
    return this.httpClient;
  }

  /**
   * Set authentication tokens
   */
  setTokens(tokens: {
    access: string;
    refresh: string;
    expires_at: number;
  }): void {
    this.httpClient.setTokens(tokens);
  }

  /**
   * Clear authentication tokens
   */
  clearTokens(): void {
    this.httpClient.clearTokens();
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  /**
   * Create a new API client instance with different configuration
   */
  static create(config: ClientConfig): APIClient {
    return new APIClient(config);
  }

  /**
   * Create API client with default configuration for development
   */
  static createDevelopment(
    baseURL: string = "http://localhost:8000/api/v1"
  ): APIClient {
    return new APIClient({
      baseURL,
      timeout: 10000,
      retries: 3,
      retryDelay: 1000,
      enableCache: true,
      defaultCacheTTL: 300000, // 5 minutes
    });
  }

  /**
   * Create API client with default configuration for production
   */
  static createProduction(baseURL: string): APIClient {
    return new APIClient({
      baseURL,
      timeout: 15000,
      retries: 5,
      retryDelay: 2000,
      enableCache: true,
      defaultCacheTTL: 600000, // 10 minutes
    });
  }
}
