/**
 * Blog service for posts, categories, tags, and comments management
 */

import { HTTPClient } from "../client";
import {
  Post,
  Category,
  Tag,
  Comment,
  CreatePostRequest,
  UpdatePostRequest,
  PostListParams,
  CreateCommentRequest,
  UpdateCommentRequest,
  CommentListParams,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  CreateTagRequest,
  UpdateTagRequest,
  PaginatedResponse,
} from "../types";

export class BlogService {
  constructor(private client: HTTPClient) {}

  // Posts Management
  /**
   * Get paginated list of blog posts
   */
  async getPosts(params?: PostListParams): Promise<PaginatedResponse<Post>> {
    const response = await this.client.get<Post[]>("/blog/posts/", params);
    return response as PaginatedResponse<Post>;
  }

  /**
   * Get single blog post by ID or slug
   */
  async getPost(identifier: number | string): Promise<Post> {
    const response = await this.client.get<Post>(`/blog/posts/${identifier}/`);
    return response.data;
  }

  /**
   * Create new blog post
   */
  async createPost(postData: CreatePostRequest): Promise<Post> {
    const response = await this.client.post<Post>("/blog/posts/", postData);
    return response.data;
  }

  /**
   * Update existing blog post
   */
  async updatePost(postId: number, postData: UpdatePostRequest): Promise<Post> {
    const response = await this.client.patch<Post>(
      `/blog/posts/${postId}/`,
      postData
    );
    return response.data;
  }

  /**
   * Delete blog post
   */
  async deletePost(postId: number): Promise<void> {
    await this.client.delete(`/blog/posts/${postId}/`);
  }

  /**
   * Publish draft post
   */
  async publishPost(postId: number, publishedAt?: string): Promise<Post> {
    const response = await this.client.post<Post>(
      `/blog/posts/${postId}/publish/`,
      {
        published_at: publishedAt,
      }
    );
    return response.data;
  }

  /**
   * Schedule post for future publication
   */
  async schedulePost(postId: number, scheduledAt: string): Promise<Post> {
    const response = await this.client.post<Post>(
      `/blog/posts/${postId}/schedule/`,
      {
        scheduled_at: scheduledAt,
      }
    );
    return response.data;
  }

  /**
   * Archive blog post
   */
  async archivePost(postId: number): Promise<Post> {
    const response = await this.client.post<Post>(
      `/blog/posts/${postId}/archive/`
    );
    return response.data;
  }

  /**
   * Like a blog post
   */
  async likePost(postId: number): Promise<void> {
    await this.client.post(`/blog/posts/${postId}/like/`);
  }

  /**
   * Unlike a blog post
   */
  async unlikePost(postId: number): Promise<void> {
    await this.client.delete(`/blog/posts/${postId}/like/`);
  }

  /**
   * Get related posts
   */
  async getRelatedPosts(postId: number, limit?: number): Promise<Post[]> {
    const params = limit ? { limit } : {};
    const response = await this.client.get<Post[]>(
      `/blog/posts/${postId}/related/`,
      params
    );
    return response.data;
  }

  /**
   * Search blog posts
   */
  async searchPosts(
    query: string,
    params?: Omit<PostListParams, "search">
  ): Promise<PaginatedResponse<Post>> {
    const searchParams = { search: query, ...params };
    const response = await this.client.get<Post[]>(
      "/blog/posts/search/",
      searchParams
    );
    return response as PaginatedResponse<Post>;
  }

  // Categories Management
  /**
   * Get all categories
   */
  async getCategories(): Promise<Category[]> {
    const response = await this.client.get<Category[]>("/blog/categories/");
    return response.data;
  }

  /**
   * Get category by ID or slug
   */
  async getCategory(identifier: number | string): Promise<Category> {
    const response = await this.client.get<Category>(
      `/blog/categories/${identifier}/`
    );
    return response.data;
  }

  /**
   * Create new category
   */
  async createCategory(categoryData: CreateCategoryRequest): Promise<Category> {
    const response = await this.client.post<Category>(
      "/blog/categories/",
      categoryData
    );
    return response.data;
  }

  /**
   * Update category
   */
  async updateCategory(
    categoryId: number,
    categoryData: UpdateCategoryRequest
  ): Promise<Category> {
    const response = await this.client.patch<Category>(
      `/blog/categories/${categoryId}/`,
      categoryData
    );
    return response.data;
  }

  /**
   * Delete category
   */
  async deleteCategory(categoryId: number): Promise<void> {
    await this.client.delete(`/blog/categories/${categoryId}/`);
  }

  /**
   * Get posts in category
   */
  async getCategoryPosts(
    categoryId: number,
    params?: PostListParams
  ): Promise<PaginatedResponse<Post>> {
    const response = await this.client.get<Post[]>(
      `/blog/categories/${categoryId}/posts/`,
      params
    );
    return response as PaginatedResponse<Post>;
  }

  // Tags Management
  /**
   * Get all tags
   */
  async getTags(): Promise<Tag[]> {
    const response = await this.client.get<Tag[]>("/blog/tags/");
    return response.data;
  }

  /**
   * Get tag by ID or slug
   */
  async getTag(identifier: number | string): Promise<Tag> {
    const response = await this.client.get<Tag>(`/blog/tags/${identifier}/`);
    return response.data;
  }

  /**
   * Create new tag
   */
  async createTag(tagData: CreateTagRequest): Promise<Tag> {
    const response = await this.client.post<Tag>("/blog/tags/", tagData);
    return response.data;
  }

  /**
   * Update tag
   */
  async updateTag(tagId: number, tagData: UpdateTagRequest): Promise<Tag> {
    const response = await this.client.patch<Tag>(
      `/blog/tags/${tagId}/`,
      tagData
    );
    return response.data;
  }

  /**
   * Delete tag
   */
  async deleteTag(tagId: number): Promise<void> {
    await this.client.delete(`/blog/tags/${tagId}/`);
  }

  /**
   * Get posts with tag
   */
  async getTagPosts(
    tagId: number,
    params?: PostListParams
  ): Promise<PaginatedResponse<Post>> {
    const response = await this.client.get<Post[]>(
      `/blog/tags/${tagId}/posts/`,
      params
    );
    return response as PaginatedResponse<Post>;
  }

  /**
   * Search tags
   */
  async searchTags(query: string): Promise<Tag[]> {
    const response = await this.client.get<Tag[]>("/blog/tags/search/", {
      search: query,
    });
    return response.data;
  }

  // Comments Management
  /**
   * Get comments for a post
   */
  async getComments(
    postId: number,
    params?: CommentListParams
  ): Promise<PaginatedResponse<Comment>> {
    const response = await this.client.get<Comment[]>(
      `/blog/posts/${postId}/comments/`,
      params
    );
    return response as PaginatedResponse<Comment>;
  }

  /**
   * Get single comment
   */
  async getComment(commentId: number): Promise<Comment> {
    const response = await this.client.get<Comment>(
      `/blog/comments/${commentId}/`
    );
    return response.data;
  }

  /**
   * Create new comment
   */
  async createComment(commentData: CreateCommentRequest): Promise<Comment> {
    const response = await this.client.post<Comment>(
      "/blog/comments/",
      commentData
    );
    return response.data;
  }

  /**
   * Update comment
   */
  async updateComment(
    commentId: number,
    commentData: UpdateCommentRequest
  ): Promise<Comment> {
    const response = await this.client.patch<Comment>(
      `/blog/comments/${commentId}/`,
      commentData
    );
    return response.data;
  }

  /**
   * Delete comment
   */
  async deleteComment(commentId: number): Promise<void> {
    await this.client.delete(`/blog/comments/${commentId}/`);
  }

  /**
   * Like a comment
   */
  async likeComment(commentId: number): Promise<void> {
    await this.client.post(`/blog/comments/${commentId}/like/`);
  }

  /**
   * Unlike a comment
   */
  async unlikeComment(commentId: number): Promise<void> {
    await this.client.delete(`/blog/comments/${commentId}/like/`);
  }

  /**
   * Approve comment (moderator only)
   */
  async approveComment(commentId: number): Promise<Comment> {
    const response = await this.client.post<Comment>(
      `/blog/comments/${commentId}/approve/`
    );
    return response.data;
  }

  /**
   * Reject comment (moderator only)
   */
  async rejectComment(commentId: number): Promise<Comment> {
    const response = await this.client.post<Comment>(
      `/blog/comments/${commentId}/reject/`
    );
    return response.data;
  }

  /**
   * Get comment replies
   */
  async getCommentReplies(
    commentId: number,
    params?: CommentListParams
  ): Promise<PaginatedResponse<Comment>> {
    const response = await this.client.get<Comment[]>(
      `/blog/comments/${commentId}/replies/`,
      params
    );
    return response as PaginatedResponse<Comment>;
  }

  // Analytics and Statistics
  /**
   * Get blog statistics
   */
  async getBlogStats(): Promise<{
    total_posts: number;
    published_posts: number;
    draft_posts: number;
    total_comments: number;
    total_views: number;
    total_likes: number;
  }> {
    const response = await this.client.get<{
      total_posts: number;
      published_posts: number;
      draft_posts: number;
      total_comments: number;
      total_views: number;
      total_likes: number;
    }>("/blog/stats/");
    return response.data;
  }

  /**
   * Get popular posts
   */
  async getPopularPosts(
    period: "day" | "week" | "month" | "year" = "week",
    limit: number = 10
  ): Promise<Post[]> {
    const response = await this.client.get<Post[]>("/blog/posts/popular/", {
      period,
      limit,
    });
    return response.data;
  }

  /**
   * Get trending tags
   */
  async getTrendingTags(limit: number = 10): Promise<Tag[]> {
    const response = await this.client.get<Tag[]>("/blog/tags/trending/", {
      limit,
    });
    return response.data;
  }

  /**
   * Get post analytics
   */
  async getPostAnalytics(postId: number): Promise<{
    views: number;
    likes: number;
    comments: number;
    shares: number;
    reading_time: number;
    bounce_rate: number;
  }> {
    const response = await this.client.get<{
      views: number;
      likes: number;
      comments: number;
      shares: number;
      reading_time: number;
      bounce_rate: number;
    }>(`/blog/posts/${postId}/analytics/`);
    return response.data;
  }
}
