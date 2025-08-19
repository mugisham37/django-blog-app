/**
 * Validation tests
 */

import {
  validateWithSchema,
  createValidator,
  ZodSchemas,
  ValidationUtils,
} from "../src/validation/validators";

describe("Schema Validation", () => {
  describe("validateWithSchema", () => {
    it("should validate valid user data", () => {
      const userData = {
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
      };

      const result = validateWithSchema("UserSchema", userData);
      expect(result.success).toBe(true);
      expect(result.data).toEqual(userData);
    });

    it("should reject invalid user data", () => {
      const invalidUserData = {
        id: "invalid", // should be number
        username: "ab", // too short
        email: "invalid-email",
        role: "invalid-role",
      };

      const result = validateWithSchema("UserSchema", invalidUserData);
      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors!.length).toBeGreaterThan(0);
    });
  });

  describe("createValidator", () => {
    it("should create a validator function", () => {
      const validateUser = createValidator("UserSchema");
      expect(typeof validateUser).toBe("function");

      const userData = {
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
      };

      const result = validateUser(userData);
      expect(result.success).toBe(true);
    });
  });
});

describe("Zod Validation", () => {
  describe("LoginRequest", () => {
    it("should validate valid login request", () => {
      const loginData = {
        email: "test@example.com",
        password: "password123",
        remember_me: true,
      };

      const result = ZodSchemas.LoginRequest.safeParse(loginData);
      expect(result.success).toBe(true);
    });

    it("should reject invalid login request", () => {
      const invalidLoginData = {
        email: "invalid-email",
        password: "123", // too short
      };

      const result = ZodSchemas.LoginRequest.safeParse(invalidLoginData);
      expect(result.success).toBe(false);
    });
  });

  describe("RegisterRequest", () => {
    it("should validate valid registration request", () => {
      const registerData = {
        username: "testuser",
        email: "test@example.com",
        password: "password123",
        password_confirm: "password123",
        terms_accepted: true,
      };

      const result = ZodSchemas.RegisterRequest.safeParse(registerData);
      expect(result.success).toBe(true);
    });

    it("should reject mismatched passwords", () => {
      const registerData = {
        username: "testuser",
        email: "test@example.com",
        password: "password123",
        password_confirm: "different123",
        terms_accepted: true,
      };

      const result = ZodSchemas.RegisterRequest.safeParse(registerData);
      expect(result.success).toBe(false);
    });
  });

  describe("PostCreateRequest", () => {
    it("should validate valid post creation request", () => {
      const postData = {
        title: "Test Post",
        content: "This is a test post content.",
        content_format: "markdown" as const,
        status: "draft" as const,
      };

      const result = ZodSchemas.PostCreateRequest.safeParse(postData);
      expect(result.success).toBe(true);
    });

    it("should apply default values", () => {
      const postData = {
        title: "Test Post",
        content: "This is a test post content.",
      };

      const result = ZodSchemas.PostCreateRequest.safeParse(postData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.content_format).toBe("markdown");
        expect(result.data.status).toBe("draft");
        expect(result.data.visibility).toBe("public");
        expect(result.data.is_featured).toBe(false);
        expect(result.data.allow_comments).toBe(true);
      }
    });
  });
});

describe("Validation Utils", () => {
  describe("isEmail", () => {
    it("should validate correct email addresses", () => {
      expect(ValidationUtils.isEmail("test@example.com")).toBe(true);
      expect(ValidationUtils.isEmail("user.name+tag@domain.co.uk")).toBe(true);
    });

    it("should reject invalid email addresses", () => {
      expect(ValidationUtils.isEmail("invalid-email")).toBe(false);
      expect(ValidationUtils.isEmail("test@")).toBe(false);
      expect(ValidationUtils.isEmail("@example.com")).toBe(false);
    });
  });

  describe("isUsername", () => {
    it("should validate correct usernames", () => {
      expect(ValidationUtils.isUsername("testuser")).toBe(true);
      expect(ValidationUtils.isUsername("test_user123")).toBe(true);
    });

    it("should reject invalid usernames", () => {
      expect(ValidationUtils.isUsername("ab")).toBe(false); // too short
      expect(ValidationUtils.isUsername("test-user")).toBe(false); // contains dash
      expect(ValidationUtils.isUsername("test user")).toBe(false); // contains space
    });
  });

  describe("generateSlug", () => {
    it("should generate valid slugs", () => {
      expect(ValidationUtils.generateSlug("Hello World")).toBe("hello-world");
      expect(ValidationUtils.generateSlug("Test Post #1")).toBe("test-post-1");
      expect(ValidationUtils.generateSlug("  Multiple   Spaces  ")).toBe(
        "multiple-spaces"
      );
    });
  });

  describe("validatePasswordStrength", () => {
    it("should score strong passwords highly", () => {
      const result =
        ValidationUtils.validatePasswordStrength("StrongP@ssw0rd123");
      expect(result.score).toBe(5);
      expect(result.feedback).toHaveLength(0);
    });

    it("should provide feedback for weak passwords", () => {
      const result = ValidationUtils.validatePasswordStrength("weak");
      expect(result.score).toBeLessThan(5);
      expect(result.feedback.length).toBeGreaterThan(0);
    });
  });

  describe("validateFileUpload", () => {
    it("should validate correct file uploads", () => {
      const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const result = ValidationUtils.validateFileUpload(mockFile);
      expect(result.success).toBe(true);
    });

    it("should reject files that are too large", () => {
      const largeContent = new Array(11 * 1024 * 1024).fill("a").join(""); // 11MB
      const mockFile = new File([largeContent], "large.jpg", {
        type: "image/jpeg",
      });
      const result = ValidationUtils.validateFileUpload(mockFile);
      expect(result.success).toBe(false);
      expect(result.errors?.[0].code).toBe("FILE_TOO_LARGE");
    });

    it("should reject invalid file types", () => {
      const mockFile = new File(["test"], "test.exe", {
        type: "application/exe",
      });
      const result = ValidationUtils.validateFileUpload(mockFile);
      expect(result.success).toBe(false);
      expect(result.errors?.[0].code).toBe("INVALID_FILE_TYPE");
    });
  });
});
