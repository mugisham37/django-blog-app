// Jest setup file for additional configuration

// Mock File constructor for Node.js environment
global.File = class File {
  constructor(bits, name, options = {}) {
    this.bits = bits;
    this.name = name;
    this.type = options.type || "";
    this.size = bits.reduce((acc, bit) => acc + (bit.length || 0), 0);
    this.lastModified = Date.now();
  }
};

// Mock console methods for cleaner test output
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeEach(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Global test utilities
global.createMockUser = (overrides = {}) => ({
  id: 1,
  username: "testuser",
  email: "test@example.com",
  role: "author",
  status: "active",
  is_verified: true,
  is_staff: false,
  is_superuser: false,
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  permissions: [],
  ...overrides,
});

global.createMockPost = (overrides = {}) => ({
  id: 1,
  title: "Test Post",
  slug: "test-post",
  content: "Test content",
  content_format: "markdown",
  author_id: 1,
  author: global.createMockUser(),
  tags: [],
  status: "published",
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
  ...overrides,
});
