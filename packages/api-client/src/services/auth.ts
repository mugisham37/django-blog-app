/**
 * Authentication service for user login, registration, and token management
 */

import { HTTPClient } from "../client";
import {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  User,
  APIResponse,
} from "../types";

export class AuthService {
  constructor(private client: HTTPClient) {}

  /**
   * Authenticate user with username/email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>(
      "/auth/login/",
      credentials
    );

    if (response.success && response.data.tokens) {
      this.client.setTokens(response.data.tokens);
    }

    return response.data;
  }

  /**
   * Register a new user account
   */
  async register(userData: RegisterRequest): Promise<User> {
    const response = await this.client.post<User>("/auth/register/", userData);
    return response.data;
  }

  /**
   * Logout current user and clear tokens
   */
  async logout(): Promise<void> {
    try {
      await this.client.post("/auth/logout/");
    } finally {
      this.client.clearTokens();
    }
  }

  /**
   * Get current authenticated user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>("/auth/me/");
    return response.data;
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<string> {
    const tokens = this.client.getTokens();
    if (!tokens?.refresh) {
      throw new Error("No refresh token available");
    }

    const response = await this.client.post<{
      access: string;
      expires_at: number;
    }>("/auth/token/refresh/", {
      refresh: tokens.refresh,
    });

    const newTokens = {
      ...tokens,
      access: response.data.access,
      expires_at: response.data.expires_at,
    };

    this.client.setTokens(newTokens);
    return response.data.access;
  }

  /**
   * Verify if current token is valid
   */
  async verifyToken(): Promise<boolean> {
    try {
      await this.client.post("/auth/token/verify/");
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Request password reset email
   */
  async forgotPassword(email: ForgotPasswordRequest): Promise<void> {
    await this.client.post("/auth/password/forgot/", email);
  }

  /**
   * Reset password using reset token
   */
  async resetPassword(resetData: ResetPasswordRequest): Promise<void> {
    await this.client.post("/auth/password/reset/", resetData);
  }

  /**
   * Change password for authenticated user
   */
  async changePassword(passwordData: ChangePasswordRequest): Promise<void> {
    await this.client.post("/auth/password/change/", passwordData);
  }

  /**
   * Activate user account using activation token
   */
  async activateAccount(token: string): Promise<void> {
    await this.client.post("/auth/activate/", { token });
  }

  /**
   * Resend activation email
   */
  async resendActivation(email: string): Promise<void> {
    await this.client.post("/auth/activate/resend/", { email });
  }

  /**
   * Enable two-factor authentication
   */
  async enableTwoFactor(): Promise<{
    qr_code: string;
    backup_codes: string[];
  }> {
    const response = await this.client.post<{
      qr_code: string;
      backup_codes: string[];
    }>("/auth/2fa/enable/");
    return response.data;
  }

  /**
   * Disable two-factor authentication
   */
  async disableTwoFactor(password: string): Promise<void> {
    await this.client.post("/auth/2fa/disable/", { password });
  }

  /**
   * Verify two-factor authentication code
   */
  async verifyTwoFactor(code: string): Promise<void> {
    await this.client.post("/auth/2fa/verify/", { code });
  }

  /**
   * Get OAuth2 authorization URL for social login
   */
  async getOAuthURL(provider: string, redirectUri?: string): Promise<string> {
    const params = redirectUri ? { redirect_uri: redirectUri } : {};
    const response = await this.client.get<{ authorization_url: string }>(
      `/auth/oauth/${provider}/`,
      params
    );
    return response.data.authorization_url;
  }

  /**
   * Complete OAuth2 authentication
   */
  async completeOAuth(
    provider: string,
    code: string,
    state?: string
  ): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>(
      `/auth/oauth/${provider}/callback/`,
      {
        code,
        state,
      }
    );

    if (response.success && response.data.tokens) {
      this.client.setTokens(response.data.tokens);
    }

    return response.data;
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated(): boolean {
    const tokens = this.client.getTokens();
    if (!tokens?.access) return false;

    // Check if token is expired
    const now = Date.now() / 1000;
    return tokens.expires_at > now;
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    const tokens = this.client.getTokens();
    return tokens?.access || null;
  }

  /**
   * Get current refresh token
   */
  getRefreshToken(): string | null {
    const tokens = this.client.getTokens();
    return tokens?.refresh || null;
  }
}
