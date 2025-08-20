/**
 * End-to-end blog functionality tests
 */
import { test, expect } from "@playwright/test";

test.describe("Blog Functionality", () => {
  test("displays blog posts on home page", async ({ page }) => {
    await page.goto("/");

    // Should show blog posts
    await expect(page.locator('[data-testid="blog-posts"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="post-card"]').first()
    ).toBeVisible();

    // Check post card content
    const firstPost = page.locator('[data-testid="post-card"]').first();
    await expect(firstPost.locator('[data-testid="post-title"]')).toBeVisible();
    await expect(
      firstPost.locator('[data-testid="post-excerpt"]')
    ).toBeVisible();
    await expect(
      firstPost.locator('[data-testid="post-author"]')
    ).toBeVisible();
    await expect(firstPost.locator('[data-testid="post-date"]')).toBeVisible();
  });

  test("can view individual blog post", async ({ page }) => {
    await page.goto("/");

    // Click on first post
    await page.locator('[data-testid="post-card"]').first().click();

    // Should navigate to post detail page
    await expect(page).toHaveURL(/\/blog\/[\w-]+/);

    // Should show post content
    await expect(page.locator('[data-testid="post-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="post-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="post-author"]')).toBeVisible();
    await expect(page.locator('[data-testid="post-meta"]')).toBeVisible();
  });

  test("can search blog posts", async ({ page }) => {
    await page.goto("/blog");

    // Enter search term
    await page.fill('[data-testid="search-input"]', "E2E Test");
    await page.press('[data-testid="search-input"]', "Enter");

    // Should show filtered results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="post-card"]')).toHaveCount(2); // We created 2 test posts

    // Clear search
    await page.fill('[data-testid="search-input"]', "");
    await page.press('[data-testid="search-input"]', "Enter");

    // Should show all posts again
    await expect(
      page.locator('[data-testid="post-card"]').count()
    ).toBeGreaterThan(2);
  });

  test("can filter posts by category", async ({ page }) => {
    await page.goto("/blog");

    // Click on a category filter
    await page.click('[data-testid="category-filter"]:has-text("Technology")');

    // Should show filtered posts
    await expect(page).toHaveURL(/category=technology/);
    await expect(page.locator('[data-testid="active-filter"]')).toContainText(
      "Technology"
    );

    // All visible posts should be in Technology category
    const posts = page.locator('[data-testid="post-card"]');
    const count = await posts.count();

    for (let i = 0; i < count; i++) {
      await expect(
        posts.nth(i).locator('[data-testid="post-category"]')
      ).toContainText("Technology");
    }
  });

  test("pagination works correctly", async ({ page }) => {
    await page.goto("/blog");

    // Check if pagination is present (assuming we have enough posts)
    const pagination = page.locator('[data-testid="pagination"]');

    if (await pagination.isVisible()) {
      const currentPage = await page
        .locator('[data-testid="current-page"]')
        .textContent();
      expect(currentPage).toBe("1");

      // Click next page
      await page.click('[data-testid="next-page"]');

      // Should navigate to page 2
      await expect(page).toHaveURL(/page=2/);
      await expect(page.locator('[data-testid="current-page"]')).toContainText(
        "2"
      );

      // Click previous page
      await page.click('[data-testid="prev-page"]');

      // Should navigate back to page 1
      await expect(page).toHaveURL(/page=1|^(?!.*page=)/);
      await expect(page.locator('[data-testid="current-page"]')).toContainText(
        "1"
      );
    }
  });
});

test.describe("Blog Post Creation", () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto("/auth/login");
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL("/dashboard");
  });

  test("can create a new blog post", async ({ page }) => {
    await page.goto("/blog/create");

    // Fill out the form
    await page.fill('[data-testid="post-title-input"]', "New E2E Test Post");
    await page.fill(
      '[data-testid="post-content-input"]',
      "This is the content of the new test post created via E2E testing."
    );

    // Select category
    await page.click('[data-testid="category-select"]');
    await page.click('[data-testid="category-option"]:has-text("Technology")');

    // Add tags
    await page.fill('[data-testid="tags-input"]', "testing, e2e, automation");

    // Set as draft first
    await page.click('[data-testid="status-draft"]');

    // Save post
    await page.click('[data-testid="save-post-button"]');

    // Should redirect to post detail or posts list
    await expect(page).toHaveURL(
      /\/blog\/new-e2e-test-post|\/dashboard\/posts/
    );

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test("validates required fields when creating post", async ({ page }) => {
    await page.goto("/blog/create");

    // Try to save without filling required fields
    await page.click('[data-testid="save-post-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="title-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="content-error"]')).toBeVisible();
  });

  test("can edit existing blog post", async ({ page }) => {
    // Navigate to posts management
    await page.goto("/dashboard/posts");

    // Click edit on first post
    await page.click('[data-testid="edit-post-button"]');

    // Should navigate to edit page
    await expect(page).toHaveURL(/\/blog\/edit\/[\w-]+/);

    // Modify the post
    await page.fill(
      '[data-testid="post-title-input"]',
      "Updated E2E Test Post"
    );
    await page.fill(
      '[data-testid="post-content-input"]',
      "This content has been updated via E2E testing."
    );

    // Save changes
    await page.click('[data-testid="save-post-button"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test("can publish and unpublish posts", async ({ page }) => {
    await page.goto("/dashboard/posts");

    // Find a draft post and publish it
    const draftPost = page
      .locator(
        '[data-testid="post-row"]:has([data-testid="post-status"]:has-text("Draft"))'
      )
      .first();

    if (await draftPost.isVisible()) {
      await draftPost.locator('[data-testid="publish-button"]').click();

      // Confirm publication
      await page.click('[data-testid="confirm-publish"]');

      // Status should change to published
      await expect(
        draftPost.locator('[data-testid="post-status"]')
      ).toContainText("Published");
    }
  });
});

test.describe("Comments System", () => {
  test("can view and add comments to blog post", async ({ page }) => {
    // Login first
    await page.goto("/auth/login");
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    // Navigate to a blog post
    await page.goto("/blog");
    await page.locator('[data-testid="post-card"]').first().click();

    // Scroll to comments section
    await page
      .locator('[data-testid="comments-section"]')
      .scrollIntoViewIfNeeded();

    // Add a new comment
    await page.fill(
      '[data-testid="comment-input"]',
      "This is a test comment added via E2E testing."
    );
    await page.click('[data-testid="submit-comment-button"]');

    // Should show the new comment
    await expect(page.locator('[data-testid="comment"]').last()).toContainText(
      "This is a test comment added via E2E testing."
    );
    await expect(
      page.locator('[data-testid="comment-author"]').last()
    ).toContainText("E2E Test");
  });

  test("shows login prompt for unauthenticated users", async ({ page }) => {
    // Navigate to blog post without logging in
    await page.goto("/blog");
    await page.locator('[data-testid="post-card"]').first().click();

    // Scroll to comments section
    await page
      .locator('[data-testid="comments-section"]')
      .scrollIntoViewIfNeeded();

    // Should show login prompt instead of comment form
    await expect(
      page.locator('[data-testid="login-to-comment"]')
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="comment-input"]')
    ).not.toBeVisible();
  });
});

test.describe("Blog SEO and Performance", () => {
  test("blog posts have proper meta tags", async ({ page }) => {
    await page.goto("/blog");
    await page.locator('[data-testid="post-card"]').first().click();

    // Check meta tags
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(10);

    const description = await page.getAttribute(
      'meta[name="description"]',
      "content"
    );
    expect(description).toBeTruthy();
    expect(description.length).toBeGreaterThan(50);

    // Check Open Graph tags
    const ogTitle = await page.getAttribute(
      'meta[property="og:title"]',
      "content"
    );
    const ogDescription = await page.getAttribute(
      'meta[property="og:description"]',
      "content"
    );
    const ogType = await page.getAttribute(
      'meta[property="og:type"]',
      "content"
    );

    expect(ogTitle).toBeTruthy();
    expect(ogDescription).toBeTruthy();
    expect(ogType).toBe("article");
  });

  test("blog pages load within performance budget", async ({ page }) => {
    // Start performance monitoring
    await page.goto("/blog");

    // Measure page load time
    const navigationTiming = await page.evaluate(() => {
      const timing = performance.getEntriesByType(
        "navigation"
      )[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded:
          timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
        loadComplete: timing.loadEventEnd - timing.loadEventStart,
        firstContentfulPaint: timing.responseEnd - timing.requestStart,
      };
    });

    // Assert performance budgets
    expect(navigationTiming.domContentLoaded).toBeLessThan(2000); // 2 seconds
    expect(navigationTiming.loadComplete).toBeLessThan(3000); // 3 seconds
  });
});
