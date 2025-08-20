/**
 * End-to-end authentication tests
 */
import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("user can register, login, and logout", async ({ page }) => {
    // Test Registration
    await page.goto("/auth/register");

    await page.fill('[data-testid="username-input"]', "newuser123");
    await page.fill('[data-testid="email-input"]', "newuser@example.com");
    await page.fill('[data-testid="password-input"]', "NewPassword123!");
    await page.fill(
      '[data-testid="password-confirm-input"]',
      "NewPassword123!"
    );
    await page.fill('[data-testid="first-name-input"]', "New");
    await page.fill('[data-testid="last-name-input"]', "User");

    await page.click('[data-testid="register-button"]');

    // Should redirect to login or dashboard
    await expect(page).toHaveURL(/\/(auth\/login|dashboard)/);

    // If redirected to login, perform login
    if (page.url().includes("/auth/login")) {
      await page.fill('[data-testid="username-input"]', "newuser123");
      await page.fill('[data-testid="password-input"]', "NewPassword123!");
      await page.click('[data-testid="login-button"]');
    }

    // Should be on dashboard
    await expect(page).toHaveURL("/dashboard");
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Test Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');

    // Should redirect to home or login
    await expect(page).toHaveURL(/\/(|auth\/login)/);
  });

  test("displays validation errors for invalid registration", async ({
    page,
  }) => {
    await page.goto("/auth/register");

    // Try to submit empty form
    await page.click('[data-testid="register-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="username-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-error"]')).toBeVisible();

    // Test weak password
    await page.fill('[data-testid="username-input"]', "testuser");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "123");
    await page.fill('[data-testid="password-confirm-input"]', "123");

    await page.click('[data-testid="register-button"]');

    await expect(page.locator('[data-testid="password-error"]')).toContainText(
      /password.*strong/i
    );
  });

  test("displays error for invalid login credentials", async ({ page }) => {
    await page.goto("/auth/login");

    await page.fill('[data-testid="username-input"]', "nonexistent");
    await page.fill('[data-testid="password-input"]', "wrongpassword");
    await page.click('[data-testid="login-button"]');

    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-error"]')).toContainText(
      /invalid.*credentials/i
    );
  });

  test("redirects to intended page after login", async ({ page }) => {
    // Try to access protected page
    await page.goto("/dashboard/profile");

    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login/);

    // Login
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    // Should redirect back to intended page
    await expect(page).toHaveURL("/dashboard/profile");
  });

  test("password reset flow works", async ({ page }) => {
    await page.goto("/auth/login");

    // Click forgot password link
    await page.click('[data-testid="forgot-password-link"]');
    await expect(page).toHaveURL("/auth/forgot-password");

    // Enter email
    await page.fill('[data-testid="email-input"]', "e2e-test@example.com");
    await page.click('[data-testid="reset-password-button"]');

    // Should show success message
    await expect(
      page.locator('[data-testid="reset-success-message"]')
    ).toBeVisible();
  });
});

test.describe("Protected Routes", () => {
  test("redirects unauthenticated users to login", async ({ page }) => {
    const protectedRoutes = [
      "/dashboard",
      "/dashboard/profile",
      "/blog/create",
      "/admin",
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/auth\/login/);
    }
  });

  test("allows authenticated users to access protected routes", async ({
    page,
  }) => {
    // Use saved auth state
    await page.goto("/auth/login");
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    // Test access to protected routes
    await page.goto("/dashboard");
    await expect(page).toHaveURL("/dashboard");

    await page.goto("/dashboard/profile");
    await expect(page).toHaveURL("/dashboard/profile");

    await page.goto("/blog/create");
    await expect(page).toHaveURL("/blog/create");
  });
});

test.describe("Session Management", () => {
  test("maintains session across page reloads", async ({ page }) => {
    // Login
    await page.goto("/auth/login");
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL("/dashboard");

    // Reload page
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL("/dashboard");
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test("handles token expiration gracefully", async ({ page }) => {
    // This test would require mocking token expiration
    // or using a short-lived token for testing

    // Login
    await page.goto("/auth/login");
    await page.fill('[data-testid="username-input"]', "e2e-test-user");
    await page.fill('[data-testid="password-input"]', "TestPassword123!");
    await page.click('[data-testid="login-button"]');

    // Mock expired token by clearing localStorage
    await page.evaluate(() => {
      localStorage.removeItem("access_token");
      localStorage.setItem("access_token", "expired-token");
    });

    // Try to access protected resource
    await page.goto("/dashboard/profile");

    // Should redirect to login due to expired token
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
