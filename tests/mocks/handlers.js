/**
 * Mock API handlers for testing
 */
import { rest } from "msw";

const API_BASE_URL = "http://localhost:8000/api/v1";

export const handlers = [
  // Authentication endpoints
  rest.post(`${API_BASE_URL}/auth/login/`, (req, res, ctx) => {
    const { username, password } = req.body;

    if (username === "testuser" && password === "testpassword") {
      return res(
        ctx.status(200),
        ctx.json({
          access_token: "mock-access-token",
          refresh_token: "mock-refresh-token",
          user: {
            id: 1,
            username: "testuser",
            email: "test@example.com",
            first_name: "Test",
            last_name: "User",
          },
        })
      );
    }

    return res(ctx.status(401), ctx.json({ error: "Invalid credentials" }));
  }),

  rest.post(`${API_BASE_URL}/auth/register/`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        user: {
          id: 2,
          username: req.body.username,
          email: req.body.email,
          first_name: req.body.first_name || "",
          last_name: req.body.last_name || "",
        },
      })
    );
  }),

  rest.post(`${API_BASE_URL}/auth/refresh/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: "new-mock-access-token",
      })
    );
  }),

  rest.get(`${API_BASE_URL}/auth/profile/`, (req, res, ctx) => {
    const authHeader = req.headers.get("Authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res(
        ctx.status(401),
        ctx.json({ error: "Authentication required" })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        id: 1,
        username: "testuser",
        email: "test@example.com",
        first_name: "Test",
        last_name: "User",
      })
    );
  }),

  // Blog endpoints
  rest.get(`${API_BASE_URL}/blog/posts/`, (req, res, ctx) => {
    const page = req.url.searchParams.get("page") || "1";
    const search = req.url.searchParams.get("search");
    const category = req.url.searchParams.get("category");

    let posts = [
      {
        id: 1,
        title: "Test Post 1",
        slug: "test-post-1",
        content: "Test content 1",
        author: { username: "testuser" },
        category: { name: "Technology", slug: "technology" },
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      },
      {
        id: 2,
        title: "Test Post 2",
        slug: "test-post-2",
        content: "Test content 2",
        author: { username: "testuser" },
        category: { name: "Science", slug: "science" },
        created_at: "2023-01-02T00:00:00Z",
        updated_at: "2023-01-02T00:00:00Z",
      },
    ];

    // Apply filters
    if (search) {
      posts = posts.filter(
        (post) =>
          post.title.toLowerCase().includes(search.toLowerCase()) ||
          post.content.toLowerCase().includes(search.toLowerCase())
      );
    }

    if (category) {
      posts = posts.filter((post) => post.category.slug === category);
    }

    return res(
      ctx.status(200),
      ctx.json({
        count: posts.length,
        next: null,
        previous: null,
        results: posts,
      })
    );
  }),

  rest.get(`${API_BASE_URL}/blog/posts/:slug/`, (req, res, ctx) => {
    const { slug } = req.params;

    const post = {
      id: 1,
      title: "Test Post",
      slug: slug,
      content: "Test content for the post",
      author: { username: "testuser" },
      category: { name: "Technology", slug: "technology" },
      tags: [{ name: "test", slug: "test" }],
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
    };

    return res(ctx.status(200), ctx.json(post));
  }),

  rest.post(`${API_BASE_URL}/blog/posts/`, (req, res, ctx) => {
    const authHeader = req.headers.get("Authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res(
        ctx.status(401),
        ctx.json({ error: "Authentication required" })
      );
    }

    return res(
      ctx.status(201),
      ctx.json({
        id: 3,
        ...req.body,
        slug: req.body.title.toLowerCase().replace(/\s+/g, "-"),
        author: { username: "testuser" },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    );
  }),

  // Comments endpoints
  rest.get(`${API_BASE_URL}/blog/posts/:slug/comments/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        count: 2,
        results: [
          {
            id: 1,
            content: "Great post!",
            author: { username: "commenter1" },
            created_at: "2023-01-01T12:00:00Z",
          },
          {
            id: 2,
            content: "Thanks for sharing!",
            author: { username: "commenter2" },
            created_at: "2023-01-01T13:00:00Z",
          },
        ],
      })
    );
  }),

  rest.post(`${API_BASE_URL}/blog/posts/:slug/comments/`, (req, res, ctx) => {
    const authHeader = req.headers.get("Authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res(
        ctx.status(401),
        ctx.json({ error: "Authentication required" })
      );
    }

    return res(
      ctx.status(201),
      ctx.json({
        id: 3,
        content: req.body.content,
        author: { username: "testuser" },
        created_at: new Date().toISOString(),
      })
    );
  }),

  // Categories and tags
  rest.get(`${API_BASE_URL}/blog/categories/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, name: "Technology", slug: "technology" },
        { id: 2, name: "Science", slug: "science" },
        { id: 3, name: "Business", slug: "business" },
      ])
    );
  }),

  rest.get(`${API_BASE_URL}/blog/tags/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, name: "JavaScript", slug: "javascript" },
        { id: 2, name: "Python", slug: "python" },
        { id: 3, name: "React", slug: "react" },
      ])
    );
  }),

  // Error handlers
  rest.get(`${API_BASE_URL}/error/500/`, (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ error: "Internal server error" }));
  }),

  rest.get(`${API_BASE_URL}/error/404/`, (req, res, ctx) => {
    return res(ctx.status(404), ctx.json({ error: "Not found" }));
  }),
];
