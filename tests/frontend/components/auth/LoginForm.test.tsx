/**
 * Login form component tests
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "../../../../apps/web/src/components/auth/LoginForm";

// Mock the auth store
const mockLogin = jest.fn();
jest.mock("../../../../apps/web/src/stores/authStore", () => ({
  useAuthStore: () => ({
    login: mockLogin,
    loading: false,
    error: null,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  it("renders login form fields", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("validates required fields", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    expect(screen.getByText(/username is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("submits form with valid data", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue({ success: true });

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/password/i), "testpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: "testuser",
        password: "testpassword",
      });
    });
  });

  it("displays error message on login failure", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/password/i), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during submission", async () => {
    const user = userEvent.setup();

    // Mock loading state
    jest
      .mocked(require("../../../../apps/web/src/stores/authStore").useAuthStore)
      .mockReturnValue({
        login: mockLogin,
        loading: true,
        error: null,
      });

    render(<LoginForm />);

    expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole("button", {
      name: /toggle password visibility/i,
    });

    expect(passwordInput).toHaveAttribute("type", "password");

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "text");

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("has proper accessibility attributes", () => {
    render(<LoginForm />);

    const form = screen.getByRole("form");
    expect(form).toHaveAttribute("aria-label", "Login form");

    const usernameInput = screen.getByLabelText(/username/i);
    expect(usernameInput).toHaveAttribute("aria-required", "true");

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute("aria-required", "true");
  });
});
