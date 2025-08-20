/**
 * Frontend-specific test setup
 */
import { configure } from "@testing-library/react";
import { server } from "../mocks/server";

// Configure React Testing Library
configure({
  testIdAttribute: "data-testid",
  asyncUtilTimeout: 5000,
});

// Setup API mocking
beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
  // Clear all mocks
  jest.clearAllMocks();
  // Clear localStorage and sessionStorage
  localStorage.clear();
  sessionStorage.clear();
});

afterAll(() => {
  server.close();
});

// Global test helpers
global.renderWithProviders = (ui, options = {}) => {
  const { preloadedState = {}, ...renderOptions } = options;

  // Import providers here to avoid circular dependencies
  const { render } = require("@testing-library/react");
  const { QueryClient, QueryClientProvider } = require("@tanstack/react-query");
  const { AuthProvider } = require("../../apps/web/src/contexts/AuthContext");

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  function Wrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock Zustand stores
jest.mock("../../apps/web/src/stores/authStore", () => ({
  useAuthStore: jest.fn(() => ({
    user: null,
    isAuthenticated: false,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
  })),
}));

jest.mock("../../apps/web/src/stores/blogStore", () => ({
  useBlogStore: jest.fn(() => ({
    posts: [],
    currentPost: null,
    loading: false,
    error: null,
    fetchPosts: jest.fn(),
    fetchPost: jest.fn(),
    createPost: jest.fn(),
    updatePost: jest.fn(),
    deletePost: jest.fn(),
  })),
}));
