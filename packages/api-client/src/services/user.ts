/**
 * User management service for profile operations and user administration
 */

import { HTTPClient } from "../client";
import {
  User,
  UserProfile,
  CreateUserRequest,
  UpdateUserRequest,
  UpdateProfileRequest,
  PaginatedResponse,
  APIResponse,
} from "../types";

export interface UserListParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: string;
  status?: string;
  ordering?: string;
  is_active?: boolean;
  is_staff?: boolean;
}

export class UserService {
  constructor(private client: HTTPClient) {}

  /**
   * Get paginated list of users (admin only)
   */
  async getUsers(params?: UserListParams): Promise<PaginatedResponse<User>> {
    const response = await this.client.get<User[]>("/users/", params);
    return response as PaginatedResponse<User>;
  }

  /**
   * Get user by ID
   */
  async getUser(userId: number): Promise<User> {
    const response = await this.client.get<User>(`/users/${userId}/`);
    return response.data;
  }

  /**
   * Create new user (admin only)
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await this.client.post<User>("/users/", userData);
    return response.data;
  }

  /**
   * Update user information
   */
  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    const response = await this.client.patch<User>(
      `/users/${userId}/`,
      userData
    );
    return response.data;
  }

  /**
   * Delete user (admin only)
   */
  async deleteUser(userId: number): Promise<void> {
    await this.client.delete(`/users/${userId}/`);
  }

  /**
   * Get user profile
   */
  async getProfile(userId?: number): Promise<UserProfile> {
    const url = userId ? `/users/${userId}/profile/` : "/users/me/profile/";
    const response = await this.client.get<UserProfile>(url);
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateProfile(
    profileData: UpdateProfileRequest,
    userId?: number
  ): Promise<UserProfile> {
    const url = userId ? `/users/${userId}/profile/` : "/users/me/profile/";
    const response = await this.client.patch<UserProfile>(url, profileData);
    return response.data;
  }

  /**
   * Upload user avatar
   */
  async uploadAvatar(
    file: File,
    userId?: number,
    onProgress?: (progress: number) => void
  ): Promise<UserProfile> {
    const url = userId ? `/users/${userId}/avatar/` : "/users/me/avatar/";
    const response = await this.client.upload<UserProfile>(
      url,
      file,
      {},
      onProgress
    );
    return response.data;
  }

  /**
   * Remove user avatar
   */
  async removeAvatar(userId?: number): Promise<void> {
    const url = userId ? `/users/${userId}/avatar/` : "/users/me/avatar/";
    await this.client.delete(url);
  }

  /**
   * Get user's activity feed
   */
  async getUserActivity(
    userId: number,
    params?: { page?: number; per_page?: number }
  ): Promise<PaginatedResponse<any>> {
    const response = await this.client.get<any[]>(
      `/users/${userId}/activity/`,
      params
    );
    return response as PaginatedResponse<any>;
  }

  /**
   * Follow a user
   */
  async followUser(userId: number): Promise<void> {
    await this.client.post(`/users/${userId}/follow/`);
  }

  /**
   * Unfollow a user
   */
  async unfollowUser(userId: number): Promise<void> {
    await this.client.delete(`/users/${userId}/follow/`);
  }

  /**
   * Get user's followers
   */
  async getFollowers(
    userId: number,
    params?: { page?: number; per_page?: number }
  ): Promise<PaginatedResponse<User>> {
    const response = await this.client.get<User[]>(
      `/users/${userId}/followers/`,
      params
    );
    return response as PaginatedResponse<User>;
  }

  /**
   * Get users that the user is following
   */
  async getFollowing(
    userId: number,
    params?: { page?: number; per_page?: number }
  ): Promise<PaginatedResponse<User>> {
    const response = await this.client.get<User[]>(
      `/users/${userId}/following/`,
      params
    );
    return response as PaginatedResponse<User>;
  }

  /**
   * Block a user
   */
  async blockUser(userId: number): Promise<void> {
    await this.client.post(`/users/${userId}/block/`);
  }

  /**
   * Unblock a user
   */
  async unblockUser(userId: number): Promise<void> {
    await this.client.delete(`/users/${userId}/block/`);
  }

  /**
   * Get blocked users
   */
  async getBlockedUsers(params?: {
    page?: number;
    per_page?: number;
  }): Promise<PaginatedResponse<User>> {
    const response = await this.client.get<User[]>(
      "/users/me/blocked/",
      params
    );
    return response as PaginatedResponse<User>;
  }

  /**
   * Search users
   */
  async searchUsers(
    query: string,
    params?: { page?: number; per_page?: number }
  ): Promise<PaginatedResponse<User>> {
    const searchParams = { search: query, ...params };
    const response = await this.client.get<User[]>(
      "/users/search/",
      searchParams
    );
    return response as PaginatedResponse<User>;
  }

  /**
   * Get user statistics (admin only)
   */
  async getUserStats(): Promise<{
    total_users: number;
    active_users: number;
    new_users_today: number;
    new_users_this_week: number;
    new_users_this_month: number;
  }> {
    const response = await this.client.get<{
      total_users: number;
      active_users: number;
      new_users_today: number;
      new_users_this_week: number;
      new_users_this_month: number;
    }>("/users/stats/");
    return response.data;
  }

  /**
   * Bulk update users (admin only)
   */
  async bulkUpdateUsers(
    userIds: number[],
    updates: Partial<UpdateUserRequest>
  ): Promise<void> {
    await this.client.post("/users/bulk-update/", {
      user_ids: userIds,
      updates,
    });
  }

  /**
   * Export users data (admin only)
   */
  async exportUsers(
    format: "csv" | "json" = "csv",
    filters?: UserListParams
  ): Promise<Blob> {
    const params = { format, ...filters };
    const response = await this.client.get("/users/export/", params);
    return new Blob([JSON.stringify(response.data)], {
      type: "application/json",
    });
  }

  /**
   * Send notification to user
   */
  async sendNotification(
    userId: number,
    notification: {
      title: string;
      message: string;
      type?: "info" | "success" | "warning" | "error";
      action_url?: string;
    }
  ): Promise<void> {
    await this.client.post(`/users/${userId}/notifications/`, notification);
  }

  /**
   * Get user notifications
   */
  async getNotifications(params?: {
    page?: number;
    per_page?: number;
    unread_only?: boolean;
  }): Promise<PaginatedResponse<any>> {
    const response = await this.client.get<any[]>(
      "/users/me/notifications/",
      params
    );
    return response as PaginatedResponse<any>;
  }

  /**
   * Mark notification as read
   */
  async markNotificationRead(notificationId: number): Promise<void> {
    await this.client.patch(`/users/me/notifications/${notificationId}/`, {
      is_read: true,
    });
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsRead(): Promise<void> {
    await this.client.post("/users/me/notifications/mark-all-read/");
  }
}
