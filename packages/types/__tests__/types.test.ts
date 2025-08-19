/**
 * Type definition tests
 */

import {
  User,
  UserRole,
  UserStatus,
  Post,
  PostStatus,
  APIResponse,
  PaginatedResponse,
  WebSocketMessage,
  WebSocketEventType,
} from "../src";

describe("Type Definitions", () => {
  describe("User Types", () => {
    it("should create valid user object", () => {
      const user: User = {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        role: UserRole.AUTHOR,
        status: UserStatus.ACTIVE,
        is_verified: true,
        is_staff: false,
        is_superuser: false,
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
        permissions: [],
      };

      expect(user.id).toBe(1);
      expect(user.role).toBe(UserRole.AUTHOR);
      expect(user.status).toBe(UserStatus.ACTIVE);
    });

    it("should handle optional fields", () => {
      const user: Partial<User> = {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        first_name: "Test",
        last_name: "User",
      };

      expect(user.first_name).toBe("Test");
      expect(user.last_name).toBe("User");
    });
  });

  describe("Blog Types", () => {
    it("should create valid post object", () => {
      const post: Post = {
        id: 1,
        title: "Test Post",
        slug: "test-post",
        content: "This is test content",
        content_format: "markdown",
        author_id: 1,
        author: {
          id: 1,
          username: "author",
          email: "author@example.com",
          full_name: "Test Author",
          role: UserRole.AUTHOR,
          status: UserStatus.ACTIVE,
          is_verified: true,
          date_joined: "2023-01-01T00:00:00Z",
          posts_count: 1,
          comments_count: 0,
        },
        tags: [],
        status: PostStatus.PUBLISHED,
        visibility: "public",
        is_featured: false,
        is_pinned: false,
        allow_comments: true,
        reading_time: 5,
        view_count: 0,
        like_count: 0,
        comment_count: 0,
        share_count: 0,
        seo: {
          robots_index: true,
          robots_follow: true,
        },
        media: [],
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      };

      expect(post.title).toBe("Test Post");
      expect(post.status).toBe(PostStatus.PUBLISHED);
      expect(post.author.role).toBe(UserRole.AUTHOR);
    });
  });

  describe("API Types", () => {
    it("should create valid API response", () => {
      const response: APIResponse<User> = {
        success: true,
        data: {
          id: 1,
          username: "testuser",
          email: "test@example.com",
          role: UserRole.AUTHOR,
          status: UserStatus.ACTIVE,
          is_verified: true,
          is_staff: false,
          is_superuser: false,
          created_at: "2023-01-01T00:00:00Z",
          updated_at: "2023-01-01T00:00:00Z",
          permissions: [],
        },
        message: "Success",
      };

      expect(response.success).toBe(true);
      expect(response.data.id).toBe(1);
      expect(response.message).toBe("Success");
    });

    it("should create valid paginated response", () => {
      const response: PaginatedResponse<User> = {
        success: true,
        data: [],
        pagination: {
          page: 1,
          pages: 1,
          per_page: 20,
          total: 0,
          has_next: false,
          has_prev: false,
        },
        message: "Success",
      };

      expect(response.success).toBe(true);
      expect(response.pagination.page).toBe(1);
      expect(response.data).toEqual([]);
    });
  });

  describe("WebSocket Types", () => {
    it("should create valid WebSocket message", () => {
      const message: WebSocketMessage<{ post_id: number }> = {
        id: "msg-123",
        type: WebSocketEventType.POST_CREATED,
        data: { post_id: 1 },
        timestamp: "2023-01-01T00:00:00Z",
        user_id: 1,
        room: "blog",
      };

      expect(message.type).toBe(WebSocketEventType.POST_CREATED);
      expect(message.data.post_id).toBe(1);
      expect(message.user_id).toBe(1);
    });
  });

  describe("Enum Values", () => {
    it("should have correct user role values", () => {
      expect(UserRole.ADMIN).toBe("admin");
      expect(UserRole.AUTHOR).toBe("author");
      expect(UserRole.SUBSCRIBER).toBe("subscriber");
    });

    it("should have correct post status values", () => {
      expect(PostStatus.DRAFT).toBe("draft");
      expect(PostStatus.PUBLISHED).toBe("published");
      expect(PostStatus.ARCHIVED).toBe("archived");
    });

    it("should have correct WebSocket event types", () => {
      expect(WebSocketEventType.POST_CREATED).toBe("post_created");
      expect(WebSocketEventType.COMMENT_CREATED).toBe("comment_created");
      expect(WebSocketEventType.USER_ONLINE).toBe("user_online");
    });
  });

  describe("Type Guards", () => {
    it("should work with type narrowing", () => {
      const response: APIResponse<User> | APIResponse<Post> = {
        success: true,
        data: {
          id: 1,
          username: "testuser",
          email: "test@example.com",
          role: UserRole.AUTHOR,
          status: UserStatus.ACTIVE,
          is_verified: true,
          is_staff: false,
          is_superuser: false,
          created_at: "2023-01-01T00:00:00Z",
          updated_at: "2023-01-01T00:00:00Z",
          permissions: [],
        },
        message: "Success",
      };

      // Type guard function
      function isUserResponse(
        res: APIResponse<User> | APIResponse<Post>
      ): res is APIResponse<User> {
        return "username" in res.data;
      }

      if (isUserResponse(response)) {
        expect(response.data.username).toBe("testuser");
      }
    });
  });

  describe("Generic Types", () => {
    it("should work with generic constraints", () => {
      interface TestEntity {
        id: number;
        name: string;
      }

      const response: APIResponse<TestEntity> = {
        success: true,
        data: {
          id: 1,
          name: "Test Entity",
        },
        message: "Success",
      };

      expect(response.data.id).toBe(1);
      expect(response.data.name).toBe("Test Entity");
    });
  });
});
