/**
 * Integration tests for the API client
 */

import { APIClient } from "../src/api-client";
import { HTTPClient } from "../src/client";

// Mock axios for integration tests
jest.mock("axios");
jest.mock("axios-retry");

const mockAxios = {
  create: jest.fn(() => mockAxiosInstance),
  post: jest.fn(),
};

const mockAxiosInstance = {
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
};

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

Object.defineProperty(window, "localStorage", {
  value: mockLocalStorage,
});

describe("APIClient Integration", () => {
  let apiClient: APIClient;

  beforeEach(() => {
    jest.clearAllMocks();
    (require("axios") as any).default = mockAxios;

    apiClient = APIClient.createDevelopment("http://localhost:8000/api/v1");
  });

  describe("authentication flow", () => {
    it("should complete full authentication flow", async () => {
      // Mock login response
      const loginResponse = {
        user: {
          id: 1,
          username: "testuser",
          email: "test@example.com",
          first_name: "Test",
          last_name: "User",
          role: "author",
          status: "active",
          is_active: true,
          is_staff: false,
          is_superuser: false,
          date_joined: "2023-01-01T00:00:00Z",
          last_login: "2023-01-01T00:00:00Z",
          profile: {
            id: 1,
            user: 1,
            avatar: null,
            bio: "",
            website: "",
            location: "",
            birth_date: null,
            social_links: {},
            preferences: {
              theme: "light",
              language: "en",
              timezone: "UTC",
              email_notifications: true,
              push_notifications: true,
              newsletter_subscription: false,
            },
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z",
          },
        },
        tokens: {
          access: "access-token-123",
          refresh: "refresh-token-123",
          expires_at: Date.now() / 1000 + 3600,
        },
      };

      mockAxiosInstance.post.mockResolvedValueOnce({
        data: {
          success: true,
          data: loginResponse,
          message: "Login successful",
        },
      });

      // Login
      const result = await apiClient.auth.login({
        username: "testuser",
        password: "password123",
      });

      expect(result).toEqual(loginResponse);
      expect(apiClient.isAuthenticated()).toBe(true);

      // Mock getCurrentUser response
      mockAxiosInstance.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: loginResponse.user,
          message: "User retrieved",
        },
      });

      // Get current user
      const user = await apiClient.auth.getCurrentUser();
      expect(user).toEqual(loginResponse.user);

      // Mock logout response
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: null, message: "Logout successful" },
      });

      // Logout
      await apiClient.auth.logout();
      expect(apiClient.isAuthenticated()).toBe(false);
    });
  });

  describe("blog operations flow", () => {
    beforeEach(() => {
      // Set up authenticated state
      apiClient.setTokens({
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600,
      });
    });

    it("should complete full blog post lifecycle", async () => {
      const postData = {
        title: "Test Post",
        content: "This is a test post content",
        excerpt: "Test excerpt",
        status: "draft" as const,
      };

      const createdPost = {
        id: 1,
        ...postData,
        slug: "test-post",
        featured_image: null,
        author: {
          id: 1,
          username: "testuser",
          first_name: "Test",
          last_name: "User",
          avatar: null,
        },
        category: null,
        tags: [],
        is_featured: false,
        view_count: 0,
        comment_count: 0,
        like_count: 0,
        published_at: null,
        scheduled_at: null,
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
        meta: {},
      };

      // Mock create post
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: createdPost, message: "Post created" },
      });

      // Create post
      const result = await apiClient.blog.createPost(postData);
      expect(result).toEqual(createdPost);

      // Mock get post
      mockAxiosInstance.get.mockResolvedValueOnce({
        data: { success: true, data: createdPost, message: "Post retrieved" },
      });

      // Get post
      const retrievedPost = await apiClient.blog.getPost(1);
      expect(retrievedPost).toEqual(createdPost);

      // Mock update post
      const updatedPost = { ...createdPost, title: "Updated Test Post" };
      mockAxiosInstance.patch.mockResolvedValueOnce({
        data: { success: true, data: updatedPost, message: "Post updated" },
      });

      // Update post
      const updateResult = await apiClient.blog.updatePost(1, {
        title: "Updated Test Post",
      });
      expect(updateResult).toEqual(updatedPost);

      // Mock publish post
      const publishedPost = {
        ...updatedPost,
        status: "published",
        published_at: "2023-01-01T12:00:00Z",
      };
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: publishedPost, message: "Post published" },
      });

      // Publish post
      const publishResult = await apiClient.blog.publishPost(1);
      expect(publishResult).toEqual(publishedPost);

      // Mock delete post
      mockAxiosInstance.delete.mockResolvedValueOnce({
        data: { success: true, data: null, message: "Post deleted" },
      });

      // Delete post
      await apiClient.blog.deletePost(1);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith("/blog/posts/1/");
    });

    it("should handle comments workflow", async () => {
      const commentData = {
        post_id: 1,
        content: "Great post!",
      };

      const createdComment = {
        id: 1,
        post: 1,
        author: {
          id: 1,
          username: "testuser",
          first_name: "Test",
          last_name: "User",
          avatar: null,
        },
        parent: null,
        content: "Great post!",
        is_approved: true,
        like_count: 0,
        reply_count: 0,
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      };

      // Mock create comment
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: {
          success: true,
          data: createdComment,
          message: "Comment created",
        },
      });

      // Create comment
      const result = await apiClient.blog.createComment(commentData);
      expect(result).toEqual(createdComment);

      // Mock get comments
      const commentsResponse = {
        success: true,
        data: [createdComment],
        message: "Comments retrieved",
        pagination: {
          page: 1,
          pages: 1,
          per_page: 20,
          total: 1,
          has_next: false,
          has_previous: false,
        },
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: commentsResponse });

      // Get comments
      const comments = await apiClient.blog.getComments(1);
      expect(comments.data).toEqual([createdComment]);

      // Mock like comment
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: null, message: "Comment liked" },
      });

      // Like comment
      await apiClient.blog.likeComment(1);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/blog/comments/1/like/"
      );
    });
  });

  describe("user management flow", () => {
    beforeEach(() => {
      // Set up authenticated state
      apiClient.setTokens({
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600,
      });
    });

    it("should handle profile management", async () => {
      const profile = {
        id: 1,
        user: 1,
        avatar: null,
        bio: "Original bio",
        website: "",
        location: "",
        birth_date: null,
        social_links: {},
        preferences: {
          theme: "light" as const,
          language: "en",
          timezone: "UTC",
          email_notifications: true,
          push_notifications: true,
          newsletter_subscription: false,
        },
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      };

      // Mock get profile
      mockAxiosInstance.get.mockResolvedValueOnce({
        data: { success: true, data: profile, message: "Profile retrieved" },
      });

      // Get profile
      const result = await apiClient.users.getProfile();
      expect(result).toEqual(profile);

      // Mock update profile
      const updatedProfile = { ...profile, bio: "Updated bio" };
      mockAxiosInstance.patch.mockResolvedValueOnce({
        data: {
          success: true,
          data: updatedProfile,
          message: "Profile updated",
        },
      });

      // Update profile
      const updateResult = await apiClient.users.updateProfile({
        bio: "Updated bio",
      });
      expect(updateResult).toEqual(updatedProfile);
    });

    it("should handle user search and social features", async () => {
      const users = [
        {
          id: 2,
          username: "otheruser",
          email: "other@example.com",
          first_name: "Other",
          last_name: "User",
          role: "author",
          status: "active",
          is_active: true,
          is_staff: false,
          is_superuser: false,
          date_joined: "2023-01-01T00:00:00Z",
          last_login: "2023-01-01T00:00:00Z",
          profile: {} as any,
        },
      ];

      // Mock search users
      const searchResponse = {
        success: true,
        data: users,
        message: "Users found",
        pagination: {
          page: 1,
          pages: 1,
          per_page: 20,
          total: 1,
          has_next: false,
          has_previous: false,
        },
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: searchResponse });

      // Search users
      const searchResult = await apiClient.users.searchUsers("other");
      expect(searchResult.data).toEqual(users);

      // Mock follow user
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: null, message: "User followed" },
      });

      // Follow user
      await apiClient.users.followUser(2);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/users/2/follow/");
    });
  });

  describe("error handling integration", () => {
    it("should handle API errors consistently", async () => {
      const apiError = {
        message: "Validation failed",
        code: "VALIDATION_ERROR",
        details: {
          title: ["This field is required"],
          content: ["This field cannot be blank"],
        },
      };

      mockAxiosInstance.post.mockRejectedValueOnce({
        response: {
          status: 422,
          data: apiError,
        },
      });

      try {
        await apiClient.blog.createPost({} as any);
        fail("Should have thrown an error");
      } catch (error) {
        expect(error).toMatchObject({
          message: "Validation failed",
          code: "VALIDATION_ERROR",
          status: 422,
          details: {
            title: ["This field is required"],
            content: ["This field cannot be blank"],
          },
        });
      }
    });
  });

  describe("caching integration", () => {
    beforeEach(() => {
      apiClient.setTokens({
        access: "access-token",
        refresh: "refresh-token",
        expires_at: Date.now() / 1000 + 3600,
      });
    });

    it("should cache GET requests and clear on mutations", async () => {
      const posts = [
        {
          id: 1,
          title: "Test Post",
          slug: "test-post",
          content: "Content",
          excerpt: "Excerpt",
          featured_image: null,
          author: {
            id: 1,
            username: "test",
            first_name: "Test",
            last_name: "User",
            avatar: null,
          },
          category: null,
          tags: [],
          status: "published",
          is_featured: false,
          view_count: 0,
          comment_count: 0,
          like_count: 0,
          published_at: "2023-01-01T00:00:00Z",
          scheduled_at: null,
          created_at: "2023-01-01T00:00:00Z",
          updated_at: "2023-01-01T00:00:00Z",
          meta: {},
        },
      ];

      // Mock first GET request
      mockAxiosInstance.get.mockResolvedValueOnce({
        data: { success: true, data: posts, message: "Posts retrieved" },
      });

      // First request - should hit API
      await apiClient.blog.getPosts();
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);

      // Second request - should use cache
      await apiClient.blog.getPosts();
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1); // Still 1, cached

      // Mock POST request (mutation)
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { success: true, data: posts[0], message: "Post created" },
      });

      // Create post - should clear cache
      await apiClient.blog.createPost({
        title: "New Post",
        content: "Content",
      });

      // Mock third GET request
      mockAxiosInstance.get.mockResolvedValueOnce({
        data: { success: true, data: posts, message: "Posts retrieved" },
      });

      // Third request - should hit API again (cache cleared)
      await apiClient.blog.getPosts();
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
    });
  });
});
