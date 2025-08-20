/**
 * Load testing script using k6
 * Tests the API under various load conditions
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

// Custom metrics
const errorRate = new Rate("errors");
const loginTrend = new Trend("login_duration");
const postListTrend = new Trend("post_list_duration");
const postDetailTrend = new Trend("post_detail_duration");

// Test configuration
export const options = {
  stages: [
    { duration: "2m", target: 10 }, // Ramp up to 10 users
    { duration: "5m", target: 10 }, // Stay at 10 users
    { duration: "2m", target: 20 }, // Ramp up to 20 users
    { duration: "5m", target: 20 }, // Stay at 20 users
    { duration: "2m", target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"], // 95% of requests must complete below 2s
    http_req_failed: ["rate<0.1"], // Error rate must be below 10%
    errors: ["rate<0.1"], // Custom error rate below 10%
    login_duration: ["p(95)<1000"], // Login should complete in <1s for 95% of requests
    post_list_duration: ["p(95)<500"], // Post listing should be fast
    post_detail_duration: ["p(95)<800"], // Post detail should load quickly
  },
};

// Base URL configuration
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/api/v1";
const WEB_URL = __ENV.WEB_URL || "http://localhost:3000";

// Test data
const testUsers = [
  { username: "loadtest1", password: "LoadTest123!" },
  { username: "loadtest2", password: "LoadTest123!" },
  { username: "loadtest3", password: "LoadTest123!" },
];

let authTokens = {};

export function setup() {
  console.log("Setting up load test...");

  // Create test users and get auth tokens
  testUsers.forEach((user, index) => {
    // Register user
    const registerPayload = {
      username: user.username,
      email: `${user.username}@loadtest.com`,
      password: user.password,
      password_confirm: user.password,
      first_name: "Load",
      last_name: `Test${index + 1}`,
    };

    const registerResponse = http.post(
      `${BASE_URL}/auth/register/`,
      JSON.stringify(registerPayload),
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    if (registerResponse.status === 201 || registerResponse.status === 400) {
      // User created or already exists, now login
      const loginPayload = {
        username: user.username,
        password: user.password,
      };

      const loginResponse = http.post(
        `${BASE_URL}/auth/login/`,
        JSON.stringify(loginPayload),
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      if (loginResponse.status === 200) {
        const loginData = JSON.parse(loginResponse.body);
        authTokens[user.username] = loginData.access_token;
        console.log(`Setup complete for user: ${user.username}`);
      }
    }
  });

  return { authTokens };
}

export default function (data) {
  // Select a random user for this iteration
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  const token = data.authTokens[user.username];

  // Test scenarios with different weights
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40% - Browse blog posts (most common scenario)
    browseBlogPosts();
  } else if (scenario < 0.7) {
    // 30% - Read specific blog post
    readBlogPost();
  } else if (scenario < 0.85) {
    // 15% - Authenticated user actions
    if (token) {
      authenticatedUserActions(token);
    } else {
      browseBlogPosts(); // Fallback to browsing
    }
  } else {
    // 15% - Search functionality
    searchBlogPosts();
  }

  sleep(1); // Think time between requests
}

function browseBlogPosts() {
  // Test blog post listing
  const listResponse = http.get(`${BASE_URL}/blog/posts/`);

  const listCheck = check(listResponse, {
    "post list status is 200": (r) => r.status === 200,
    "post list has results": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results && Array.isArray(body.results);
      } catch (e) {
        return false;
      }
    },
  });

  postListTrend.add(listResponse.timings.duration);
  errorRate.add(!listCheck);

  // Test categories
  const categoriesResponse = http.get(`${BASE_URL}/blog/categories/`);
  check(categoriesResponse, {
    "categories status is 200": (r) => r.status === 200,
  });

  // Test tags
  const tagsResponse = http.get(`${BASE_URL}/blog/tags/`);
  check(tagsResponse, {
    "tags status is 200": (r) => r.status === 200,
  });
}

function readBlogPost() {
  // First get the list to find a post
  const listResponse = http.get(`${BASE_URL}/blog/posts/?page_size=5`);

  if (listResponse.status === 200) {
    try {
      const listData = JSON.parse(listResponse.body);
      if (listData.results && listData.results.length > 0) {
        const randomPost =
          listData.results[Math.floor(Math.random() * listData.results.length)];

        // Get post detail
        const detailResponse = http.get(
          `${BASE_URL}/blog/posts/${randomPost.slug}/`
        );

        const detailCheck = check(detailResponse, {
          "post detail status is 200": (r) => r.status === 200,
          "post detail has content": (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.title && body.content;
            } catch (e) {
              return false;
            }
          },
        });

        postDetailTrend.add(detailResponse.timings.duration);
        errorRate.add(!detailCheck);

        // Get comments for the post
        const commentsResponse = http.get(
          `${BASE_URL}/blog/posts/${randomPost.slug}/comments/`
        );
        check(commentsResponse, {
          "comments status is 200": (r) => r.status === 200,
        });
      }
    } catch (e) {
      errorRate.add(true);
    }
  }
}

function authenticatedUserActions(token) {
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // Get user profile
  const profileResponse = http.get(`${BASE_URL}/auth/profile/`, { headers });
  check(profileResponse, {
    "profile status is 200": (r) => r.status === 200,
  });

  // Create a test post
  const postPayload = {
    title: `Load Test Post ${Date.now()}`,
    content: "This is a test post created during load testing.",
    status: "draft",
  };

  const createResponse = http.post(
    `${BASE_URL}/blog/posts/`,
    JSON.stringify(postPayload),
    { headers }
  );
  const createCheck = check(createResponse, {
    "post creation status is 201": (r) => r.status === 201,
  });

  if (createCheck && createResponse.status === 201) {
    try {
      const createdPost = JSON.parse(createResponse.body);

      // Update the post
      const updatePayload = {
        title: `Updated ${createdPost.title}`,
        status: "published",
      };

      const updateResponse = http.patch(
        `${BASE_URL}/blog/posts/${createdPost.slug}/`,
        JSON.stringify(updatePayload),
        { headers }
      );
      check(updateResponse, {
        "post update status is 200": (r) => r.status === 200,
      });

      // Add a comment
      const commentPayload = {
        content: "This is a test comment from load testing.",
      };

      const commentResponse = http.post(
        `${BASE_URL}/blog/posts/${createdPost.slug}/comments/`,
        JSON.stringify(commentPayload),
        { headers }
      );
      check(commentResponse, {
        "comment creation status is 201": (r) => r.status === 201,
      });

      // Clean up - delete the post
      const deleteResponse = http.del(
        `${BASE_URL}/blog/posts/${createdPost.slug}/`,
        null,
        { headers }
      );
      check(deleteResponse, {
        "post deletion status is 204": (r) => r.status === 204,
      });
    } catch (e) {
      errorRate.add(true);
    }
  }
}

function searchBlogPosts() {
  const searchTerms = ["test", "blog", "api", "load", "performance"];
  const searchTerm =
    searchTerms[Math.floor(Math.random() * searchTerms.length)];

  const searchResponse = http.get(
    `${BASE_URL}/blog/posts/?search=${searchTerm}`
  );

  const searchCheck = check(searchResponse, {
    "search status is 200": (r) => r.status === 200,
    "search returns results": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  errorRate.add(!searchCheck);
}

export function teardown(data) {
  console.log("Cleaning up load test...");

  // Clean up any remaining test data
  Object.keys(data.authTokens).forEach((username) => {
    const token = data.authTokens[username];
    const headers = {
      Authorization: `Bearer ${token}`,
    };

    // Get user's posts and delete test posts
    const postsResponse = http.get(
      `${BASE_URL}/blog/posts/?author=${username}`,
      { headers }
    );

    if (postsResponse.status === 200) {
      try {
        const postsData = JSON.parse(postsResponse.body);
        postsData.results.forEach((post) => {
          if (post.title.includes("Load Test")) {
            http.del(`${BASE_URL}/blog/posts/${post.slug}/`, null, { headers });
          }
        });
      } catch (e) {
        console.log(`Error cleaning up posts for ${username}:`, e);
      }
    }
  });

  console.log("Load test cleanup complete");
}
