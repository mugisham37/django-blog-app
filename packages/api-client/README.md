# Enterprise API Client

A comprehensive TypeScript API client for Django backend services with automatic token refresh, request/response caching, and error handling.

## Features

- 🔐 **Automatic Authentication** - JWT token management with automatic refresh
- 🚀 **Request/Response Caching** - Configurable caching with TTL support
- 🔄 **Automatic Retries** - Configurable retry logic for failed requests
- 📝 **Request/Response Logging** - Comprehensive logging with sanitization
- 🛡️ **Error Handling** - Standardized error handling with custom error types
- 📤 **File Upload** - Support for file uploads with progress tracking
- 🌐 **Offline Support** - Request caching and offline data synchronization
- 🎯 **Type Safety** - Full TypeScript support with generated types

## Installation

```bash
npm install @enterprise/api-client
```

## Quick Start

```typescript
import { APIClient } from "@enterprise/api-client";

// Create API client instance
const apiClient = APIClient.createDevelopment("http://localhost:8000/api/v1");

// Login user
const loginResponse = await apiClient.auth.login({
  username: "user@example.com",
  password: "password123",
});

// Get current user
const user = await apiClient.auth.getCurrentUser();

// Get blog posts
const posts = await apiClient.blog.getPosts({
  page: 1,
  per_page: 10,
  status: "published",
});

// Create new post
const newPost = await apiClient.blog.createPost({
  title: "My New Post",
  content: "Post content here...",
  status: "draft",
});
```

## Configuration

### Basic Configuration

```typescript
import { APIClient } from "@enterprise/api-client";

const apiClient = new APIClient({
  baseURL: "https://api.example.com/v1",
  timeout: 10000,
  retries: 3,
  retryDelay: 1000,
  enableCache: true,
  defaultCacheTTL: 300000, // 5 minutes
});
```

### Environment-Specific Configurations

```typescript
// Development
const devClient = APIClient.createDevelopment("http://localhost:8000/api/v1");

// Production
const prodClient = APIClient.createProduction("https://api.example.com/v1");
```

## Authentication

### Login and Token Management

```typescript
// Login
const response = await apiClient.auth.login({
  username: "user@example.com",
  password: "password123",
  remember_me: true,
});

// Check authentication status
const isAuthenticated = apiClient.isAuthenticated();

// Get current user
const user = await apiClient.auth.getCurrentUser();

// Logout
await apiClient.auth.logout();
```

### Token Refresh

The client automatically handles token refresh when receiving 401 responses:

```typescript
// Tokens are automatically refreshed when needed
const user = await apiClient.auth.getCurrentUser();

// Manual token refresh
const newAccessToken = await apiClient.auth.refreshToken();
```

### Two-Factor Authentication

```typescript
// Enable 2FA
const { qr_code, backup_codes } = await apiClient.auth.enableTwoFactor();

// Verify 2FA code
await apiClient.auth.verifyTwoFactor("123456");

// Disable 2FA
await apiClient.auth.disableTwoFactor("password");
```

### Social Authentication

```typescript
// Get OAuth URL
const authUrl = await apiClient.auth.getOAuthURL(
  "google",
  "http://localhost:3000/callback"
);

// Complete OAuth flow
const loginResponse = await apiClient.auth.completeOAuth(
  "google",
  "auth_code",
  "state"
);
```

## User Management

### User Operations

```typescript
// Get users (admin only)
const users = await apiClient.users.getUsers({
  page: 1,
  per_page: 20,
  search: "john",
  role: "author",
});

// Get user by ID
const user = await apiClient.users.getUser(123);

// Create user (admin only)
const newUser = await apiClient.users.createUser({
  username: "newuser",
  email: "new@example.com",
  password: "password123",
  role: "author",
});

// Update user
const updatedUser = await apiClient.users.updateUser(123, {
  first_name: "John",
  last_name: "Doe",
});
```

### Profile Management

```typescript
// Get profile
const profile = await apiClient.users.getProfile();

// Update profile
const updatedProfile = await apiClient.users.updateProfile({
  bio: "Updated bio",
  website: "https://example.com",
  social_links: {
    twitter: "@username",
    github: "username",
  },
});

// Upload avatar
const profile = await apiClient.users.uploadAvatar(
  avatarFile,
  undefined,
  (progress) => console.log(`Upload progress: ${progress}%`)
);
```

### Social Features

```typescript
// Follow user
await apiClient.users.followUser(123);

// Get followers
const followers = await apiClient.users.getFollowers(123);

// Get following
const following = await apiClient.users.getFollowing(123);

// Block user
await apiClient.users.blockUser(123);
```

## Blog Management

### Posts

```typescript
// Get posts with filtering
const posts = await apiClient.blog.getPosts({
  page: 1,
  per_page: 10,
  status: "published",
  category: "technology",
  tag: "javascript",
  search: "react",
  ordering: "-created_at",
});

// Get single post
const post = await apiClient.blog.getPost("my-post-slug");

// Create post
const newPost = await apiClient.blog.createPost({
  title: "My New Post",
  content: "Post content...",
  excerpt: "Short description",
  category_id: 1,
  tag_ids: [1, 2, 3],
  status: "draft",
  meta: {
    seo_title: "SEO Title",
    seo_description: "SEO Description",
  },
});

// Update post
const updatedPost = await apiClient.blog.updatePost(123, {
  title: "Updated Title",
  status: "published",
});

// Publish post
const publishedPost = await apiClient.blog.publishPost(123);

// Schedule post
const scheduledPost = await apiClient.blog.schedulePost(
  123,
  "2024-01-01T10:00:00Z"
);
```

### Categories and Tags

```typescript
// Get categories
const categories = await apiClient.blog.getCategories();

// Create category
const category = await apiClient.blog.createCategory({
  name: "Technology",
  description: "Tech-related posts",
  parent_id: null,
});

// Get tags
const tags = await apiClient.blog.getTags();

// Search tags
const searchResults = await apiClient.blog.searchTags("javascript");
```

### Comments

```typescript
// Get comments for post
const comments = await apiClient.blog.getComments(123, {
  page: 1,
  per_page: 20,
  approved: true,
});

// Create comment
const comment = await apiClient.blog.createComment({
  post_id: 123,
  content: "Great post!",
  parent_id: null, // For replies
});

// Like comment
await apiClient.blog.likeComment(456);

// Approve comment (moderator)
await apiClient.blog.approveComment(456);
```

## Error Handling

### Error Types

```typescript
import {
  isAPIError,
  isValidationError,
  isAuthError,
} from "@enterprise/api-client";

try {
  await apiClient.blog.createPost(invalidData);
} catch (error) {
  if (isAPIError(error)) {
    console.log("API Error:", error.message);
    console.log("Error Code:", error.code);
    console.log("Status:", error.status);

    if (isValidationError(error)) {
      console.log("Validation errors:", error.details);
    }

    if (isAuthError(error)) {
      // Redirect to login
      window.location.href = "/login";
    }
  }
}
```

### Global Error Handling

```typescript
const apiClient = new APIClient({
  baseURL: "https://api.example.com/v1",
  // ... other config
});

// Add global error handler
apiClient.getHTTPClient().interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling logic
    if (error.status === 401) {
      // Redirect to login
    } else if (error.status >= 500) {
      // Show server error message
    }
    return Promise.reject(error);
  }
);
```

## Caching

### Request Caching

```typescript
// Cache enabled by default for GET requests
const posts = await apiClient.blog.getPosts(); // Cached

// Disable cache for specific request
const freshPosts = await apiClient.blog.getPosts({}, { cache: false });

// Custom cache TTL
const posts = await apiClient.blog.getPosts({}, { cacheTTL: 600000 }); // 10 minutes
```

### Cache Management

```typescript
// Clear all cache
apiClient.getHTTPClient().clearCache();

// Cache is automatically cleared on mutations (POST, PUT, PATCH, DELETE)
await apiClient.blog.createPost(postData); // Clears cache
```

## File Uploads

```typescript
// Upload with progress tracking
const result = await apiClient.users.uploadAvatar(
  file,
  undefined,
  (progress) => {
    console.log(`Upload progress: ${progress}%`);
    // Update progress bar
  }
);

// Generic file upload
const response = await apiClient
  .getHTTPClient()
  .upload("/upload-endpoint", file, { additional: "data" }, (progress) =>
    console.log(progress)
  );
```

## Advanced Usage

### Custom Interceptors

```typescript
import {
  AuthInterceptor,
  LoggingInterceptor,
  ErrorInterceptor,
} from "@enterprise/api-client";

const httpClient = apiClient.getHTTPClient();

// Add custom logging
const loggingInterceptor = new LoggingInterceptor({
  enableRequestLogging: true,
  enableResponseLogging: true,
  logLevel: "debug",
  onLog: (logData) => {
    // Send to external logging service
    console.log("API Log:", logData);
  },
});

httpClient.interceptors.request.use(loggingInterceptor.onRequest);
httpClient.interceptors.response.use(
  loggingInterceptor.onResponse,
  loggingInterceptor.onResponseError
);
```

### Custom Services

```typescript
class CustomService {
  constructor(private client: HTTPClient) {}

  async customEndpoint(data: any) {
    return this.client.post("/custom-endpoint", data);
  }
}

// Add to API client
const customService = new CustomService(apiClient.getHTTPClient());
```

## TypeScript Support

The package includes comprehensive TypeScript definitions:

```typescript
import type {
  User,
  Post,
  Comment,
  Category,
  Tag,
  APIResponse,
  PaginatedResponse,
  CreatePostRequest,
  UpdatePostRequest,
} from "@enterprise/api-client";

// Type-safe API calls
const posts: PaginatedResponse<Post> = await apiClient.blog.getPosts();
const user: User = await apiClient.auth.getCurrentUser();
```

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## Development

```bash
# Install dependencies
npm install

# Build package
npm run build

# Build in watch mode
npm run build:watch

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
