/**
 * Global setup for Playwright tests
 */
import { chromium, FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig) {
  console.log("🚀 Starting global setup...");

  // Create a browser instance for setup
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Wait for the web server to be ready
    console.log("⏳ Waiting for web server...");
    await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
    console.log("✅ Web server is ready");

    // Wait for the API server to be ready
    console.log("⏳ Waiting for API server...");
    const apiResponse = await page.request.get(
      "http://localhost:8000/api/v1/health/"
    );
    if (apiResponse.ok()) {
      console.log("✅ API server is ready");
    } else {
      console.log("⚠️ API server health check failed, but continuing...");
    }

    // Create test data if needed
    await setupTestData(page);

    // Authenticate and save auth state for tests that need it
    await setupAuthState(page);
  } catch (error) {
    console.error("❌ Global setup failed:", error);
    throw error;
  } finally {
    await browser.close();
  }

  console.log("✅ Global setup completed");
}

async function setupTestData(page: any) {
  console.log("📝 Setting up test data...");

  try {
    // Create test user via API
    const registerResponse = await page.request.post(
      "http://localhost:8000/api/v1/auth/register/",
      {
        data: {
          username: "e2e-test-user",
          email: "e2e-test@example.com",
          password: "TestPassword123!",
          password_confirm: "TestPassword123!",
          first_name: "E2E",
          last_name: "Test",
        },
      }
    );

    if (registerResponse.ok()) {
      console.log("✅ Test user created");
    } else {
      console.log("ℹ️ Test user might already exist");
    }

    // Create test blog posts
    const loginResponse = await page.request.post(
      "http://localhost:8000/api/v1/auth/login/",
      {
        data: {
          username: "e2e-test-user",
          password: "TestPassword123!",
        },
      }
    );

    if (loginResponse.ok()) {
      const { access_token } = await loginResponse.json();

      // Create test posts
      const testPosts = [
        {
          title: "E2E Test Post 1",
          content: "This is the first test post for E2E testing.",
          status: "published",
        },
        {
          title: "E2E Test Post 2",
          content: "This is the second test post for E2E testing.",
          status: "published",
        },
      ];

      for (const post of testPosts) {
        await page.request.post("http://localhost:8000/api/v1/blog/posts/", {
          data: post,
          headers: {
            Authorization: `Bearer ${access_token}`,
          },
        });
      }

      console.log("✅ Test blog posts created");
    }
  } catch (error) {
    console.log("⚠️ Test data setup failed, but continuing:", error.message);
  }
}

async function setupAuthState(page: any) {
  console.log("🔐 Setting up authentication state...");

  try {
    // Navigate to login page
    await page.goto("http://localhost:3000/auth/login");

    // Fill login form
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    // Wait for successful login
    await page.waitForURL("http://localhost:3000/dashboard", {
      timeout: 10000,
    });

    // Save authentication state
    await page.context().storageState({ path: "tests/e2e/auth-state.json" });

    console.log("✅ Authentication state saved");
  } catch (error) {
    console.log("⚠️ Authentication setup failed:", error.message);
  }
}

export default globalSetup;
