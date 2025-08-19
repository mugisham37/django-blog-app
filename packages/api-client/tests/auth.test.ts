/**
 * Tests for the authentication service
 */

import { AuthService } from "../src/services/auth";
import { HTTPClient } from "../src/client";
import { LoginRequest, RegisterRequest, LoginResponse } from "../src/types";

// Mock HTTPClient
jest.mock("../src/client");

describe("AuthService", () => {
  let authService: AuthService;
  let mockClient: jest.Mocked<HTTPClient>;

  beforeEach(() => {
    mockClient = {
      post: jest.fn(),
      get: jest.fn(),
      setTokens: jest.fn(),
      clearTokens: jest.fn(),
      getTokens: jest.fn(),
    } as any;

    authService = new AuthService(mockClient);
  });

  describe("login", () => {
    const loginRequest: LoginRequest = {
      username: "testuser",
      password: "testpass",
    };

    const loginResponse: LoginResponse = {
      user: {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        first_name: "Test",
        last_name: "User",
        role: "author" as any,
        status: "active" as any,
        is_active: true,
        is_staff: false,
        is_superuser: false,
        date_joined: "2023-01-01T00:00:00Z",
        last_login: "2023-01-01T00:00:00Z",
        profile: {} as any,
      },
      tokens: {
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600,
      },
    };

    it("should login successfully and set tokens", async () => {
      mockClient.post.mockResolvedValue({
        success: true,
        data: loginResponse,
        message: "Login successful",
      });

      const result = await authService.login(loginRequest);

      expect(mockClient.post).toHaveBeenCalledWith(
        "/auth/login/",
        loginRequest
      );
      expect(mockClient.setTokens).toHaveBeenCalledWith(loginResponse.tokens);
      expect(result).toEqual(loginResponse);
    });

    it("should handle login failure", async () => {
      const error = new Error("Invalid credentials");
      mockClient.post.mockRejectedValue(error);

      await expect(authService.login(loginRequest)).rejects.toThrow(
        "Invalid credentials"
      );
      expect(mockClient.setTokens).not.toHaveBeenCalled();
    });
  });

  describe("register", () => {
    const registerRequest: RegisterRequest = {
      username: "newuser",
      email: "new@example.com",
      password: "newpass",
      confirm_password: "newpass",
    };

    it("should register successfully", async () => {
      const user = {
        id: 2,
        username: "newuser",
        email: "new@example.com",
      };

      mockClient.post.mockResolvedValue({
        success: true,
        data: user,
        message: "Registration successful",
      });

      const result = await authService.register(registerRequest);

      expect(mockClient.post).toHaveBeenCalledWith(
        "/auth/register/",
        registerRequest
      );
      expect(result).toEqual(user);
    });
  });

  describe("logout", () => {
    it("should logout and clear tokens", async () => {
      mockClient.post.mockResolvedValue({
        success: true,
        data: null,
        message: "Logout successful",
      });

      await authService.logout();

      expect(mockClient.post).toHaveBeenCalledWith("/auth/logout/");
      expect(mockClient.clearTokens).toHaveBeenCalled();
    });

    it("should clear tokens even if logout request fails", async () => {
      mockClient.post.mockRejectedValue(new Error("Network error"));

      await authService.logout();

      expect(mockClient.clearTokens).toHaveBeenCalled();
    });
  });

  describe("getCurrentUser", () => {
    it("should get current user", async () => {
      const user = {
        id: 1,
        username: "testuser",
        email: "test@example.com",
      };

      mockClient.get.mockResolvedValue({
        success: true,
        data: user,
        message: "User retrieved",
      });

      const result = await authService.getCurrentUser();

      expect(mockClient.get).toHaveBeenCalledWith("/auth/me/");
      expect(result).toEqual(user);
    });
  });

  describe("refreshToken", () => {
    it("should refresh token successfully", async () => {
      const tokens = {
        access: "old-access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600,
      };

      const newTokenData = {
        access: "new-access-token",
        expires_at: Date.now() / 1000 + 3600,
      };

      mockClient.getTokens.mockReturnValue(tokens);
      mockClient.post.mockResolvedValue({
        success: true,
        data: newTokenData,
        message: "Token refreshed",
      });

      const result = await authService.refreshToken();

      expect(mockClient.post).toHaveBeenCalledWith("/auth/token/refresh/", {
        refresh: tokens.refresh,
      });
      expect(mockClient.setTokens).toHaveBeenCalledWith({
        ...tokens,
        access: newTokenData.access,
        expires_at: newTokenData.expires_at,
      });
      expect(result).toBe(newTokenData.access);
    });

    it("should throw error if no refresh token", async () => {
      mockClient.getTokens.mockReturnValue(null);

      await expect(authService.refreshToken()).rejects.toThrow(
        "No refresh token available"
      );
    });
  });

  describe("isAuthenticated", () => {
    it("should return true for valid token", () => {
      const tokens = {
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600, // 1 hour from now
      };

      mockClient.getTokens.mockReturnValue(tokens);

      expect(authService.isAuthenticated()).toBe(true);
    });

    it("should return false for expired token", () => {
      const tokens = {
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 - 3600, // 1 hour ago
      };

      mockClient.getTokens.mockReturnValue(tokens);

      expect(authService.isAuthenticated()).toBe(false);
    });

    it("should return false for no tokens", () => {
      mockClient.getTokens.mockReturnValue(null);

      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe("verifyToken", () => {
    it("should return true for valid token", async () => {
      mockClient.post.mockResolvedValue({
        success: true,
        data: null,
        message: "Token valid",
      });

      const result = await authService.verifyToken();

      expect(mockClient.post).toHaveBeenCalledWith("/auth/token/verify/");
      expect(result).toBe(true);
    });

    it("should return false for invalid token", async () => {
      mockClient.post.mockRejectedValue(new Error("Invalid token"));

      const result = await authService.verifyToken();

      expect(result).toBe(false);
    });
  });

  describe("password management", () => {
    it("should request password reset", async () => {
      mockClient.post.mockResolvedValue({
        success: true,
        data: null,
        message: "Reset email sent",
      });

      await authService.forgotPassword({ email: "test@example.com" });

      expect(mockClient.post).toHaveBeenCalledWith("/auth/password/forgot/", {
        email: "test@example.com",
      });
    });

    it("should reset password", async () => {
      const resetData = {
        token: "reset-token",
        password: "newpass",
        confirm_password: "newpass",
      };

      mockClient.post.mockResolvedValue({
        success: true,
        data: null,
        message: "Password reset",
      });

      await authService.resetPassword(resetData);

      expect(mockClient.post).toHaveBeenCalledWith(
        "/auth/password/reset/",
        resetData
      );
    });

    it("should change password", async () => {
      const passwordData = {
        old_password: "oldpass",
        new_password: "newpass",
        confirm_password: "newpass",
      };

      mockClient.post.mockResolvedValue({
        success: true,
        data: null,
        message: "Password changed",
      });

      await authService.changePassword(passwordData);

      expect(mockClient.post).toHaveBeenCalledWith(
        "/auth/password/change/",
        passwordData
      );
    });
  });
});
