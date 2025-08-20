/**
 * Global teardown for Playwright tests
 */
import { chromium, FullConfig } from "@playwright/test";
import fs from "fs";
import path from "path";

async function globalTeardown(config: FullConfig) {
  console.log("🧹 Starting global teardown...");

  try {
    // Clean up test data
    await cleanupTestData();

    // Clean up auth state file
    const authStatePath = path.join(__dirname, "auth-state.json");
    if (fs.existsSync(authStatePath)) {
      fs.unlinkSync(authStatePath);
      console.log("✅ Auth state file cleaned up");
    }

    // Clean up any temporary files
    await cleanupTempFiles();
  } catch (error) {
    console.error("❌ Global teardown failed:", error);
  }

  console.log("✅ Global teardown completed");
}

async function cleanupTestData() {
  console.log("🗑️ Cleaning up test data...");

  try {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    // Login as test user to get auth token
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

      // Delete test posts
      const postsResponse = await page.request.get(
        "http://localhost:8000/api/v1/blog/posts/",
        {
          headers: {
            Authorization: `Bearer ${access_token}`,
          },
        }
      );

      if (postsResponse.ok()) {
        const { results: posts } = await postsResponse.json();

        for (const post of posts) {
          if (post.title.startsWith("E2E Test")) {
            await page.request.delete(
              `http://localhost:8000/api/v1/blog/posts/${post.slug}/`,
              {
                headers: {
                  Authorization: `Bearer ${access_token}`,
                },
              }
            );
          }
        }
      }

      // Note: In a real scenario, you might want to keep the test user
      // or have a separate cleanup endpoint for test data
    }

    await browser.close();
    console.log("✅ Test data cleaned up");
  } catch (error) {
    console.log("⚠️ Test data cleanup failed:", error.message);
  }
}

async function cleanupTempFiles() {
  console.log("📁 Cleaning up temporary files...");

  try {
    const tempDirs = [
      "tests/reports/playwright-artifacts",
      "tests/reports/screenshots",
      "tests/reports/videos",
    ];

    for (const dir of tempDirs) {
      if (fs.existsSync(dir)) {
        // Clean old files (older than 7 days)
        const files = fs.readdirSync(dir);
        const now = Date.now();
        const weekAgo = now - 7 * 24 * 60 * 60 * 1000;

        for (const file of files) {
          const filePath = path.join(dir, file);
          const stats = fs.statSync(filePath);

          if (stats.mtime.getTime() < weekAgo) {
            fs.unlinkSync(filePath);
          }
        }
      }
    }

    console.log("✅ Temporary files cleaned up");
  } catch (error) {
    console.log("⚠️ Temporary file cleanup failed:", error.message);
  }
}

export default globalTeardown;
