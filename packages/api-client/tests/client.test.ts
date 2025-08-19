/**
 * Tests for the HTTP client
 */

import { HTTPClient } from "../src/client";
import { AuthTokens } from "../src/types";

// Mock axios
jest.mock("axios");
jest.mock("axios-retry");

const mockAxios = {
  create: jest.fn(() => mockAxiosInstance),
  post: jest.fn(),
};

const mockAxiosInstance = {
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
};

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

Object.defineProperty(window, "localStorage", {
  value: mockLocalStorage,
});

describe("HTTPClient", () => {
  let client: HTTPClient;

  beforeEach(() => {
    jest.clearAllMocks();
    (require("axios") as any).default = mockAxios;

    client = new HTTPClient({
      baseURL: "http://localhost:8000/api/v1",
    });
  });

  describe("constructor", () => {
    it("should create axios instance with correct config", () => {
      expect(mockAxios.create).toHaveBeenCalledWith({
        baseURL: "http://localhost:8000/api/v1",
        timeout: 10000,
        paramsSerializer: expect.any(Function),
      });
    });

    it("should setup interceptors", () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe("token management", () => {
    const mockTokens: AuthTokens = {
      access: "access-token",
      refresh: "refresh-token",
      expires_at: Date.now() / 1000 + 3600,
    };

    it("should set tokens", () => {
      client.setTokens(mockTokens);
      expect(client.getTokens()).toEqual(mockTokens);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "auth_tokens",
        JSON.stringify(mockTokens)
      );
    });

    it("should clear tokens", () => {
      client.setTokens(mockTokens);
      client.clearTokens();
      expect(client.getTokens()).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith("auth_tokens");
    });

    it("should load tokens from storage", () => {
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockTokens));

      const newClient = new HTTPClient({
        baseURL: "http://localhost:8000/api/v1",
      });

      expect(newClient.getTokens()).toEqual(mockTokens);
    });
  });

  describe("HTTP methods", () => {
    beforeEach(() => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { success: true, data: "test" },
      });
      mockAxiosInstance.post.mockResolvedValue({
        data: { success: true, data: "test" },
      });
      mockAxiosInstance.put.mockResolvedValue({
        data: { success: true, data: "test" },
      });
      mockAxiosInstance.patch.mockResolvedValue({
        data: { success: true, data: "test" },
      });
      mockAxiosInstance.delete.mockResolvedValue({
        data: { success: true, data: "test" },
      });
    });

    it("should make GET request", async () => {
      const result = await client.get("/test", { param: "value" });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/test", {
        params: { param: "value" },
      });
      expect(result).toEqual({ success: true, data: "test" });
    });

    it("should make POST request", async () => {
      const data = { key: "value" };
      const result = await client.post("/test", data);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/test", data);
      expect(result).toEqual({ success: true, data: "test" });
    });

    it("should make PUT request", async () => {
      const data = { key: "value" };
      const result = await client.put("/test", data);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith("/test", data);
      expect(result).toEqual({ success: true, data: "test" });
    });

    it("should make PATCH request", async () => {
      const data = { key: "value" };
      const result = await client.patch("/test", data);

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith("/test", data);
      expect(result).toEqual({ success: true, data: "test" });
    });

    it("should make DELETE request", async () => {
      const result = await client.delete("/test");

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith("/test");
      expect(result).toEqual({ success: true, data: "test" });
    });
  });

  describe("caching", () => {
    beforeEach(() => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { success: true, data: "test" },
      });
    });

    it("should cache GET requests by default", async () => {
      await client.get("/test");
      await client.get("/test");

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
    });

    it("should not cache when cache is disabled", async () => {
      await client.get("/test", {}, { cache: false });
      await client.get("/test", {}, { cache: false });

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
    });
  });

  describe("file upload", () => {
    it("should upload file with progress callback", async () => {
      const file = new File(["content"], "test.txt", { type: "text/plain" });
      const onProgress = jest.fn();

      mockAxiosInstance.post.mockResolvedValue({
        data: { success: true, data: "uploaded" },
      });

      const result = await client.upload(
        "/upload",
        file,
        { key: "value" },
        onProgress
      );

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/upload",
        expect.any(FormData),
        expect.objectContaining({
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: expect.any(Function),
        })
      );
      expect(result).toEqual({ success: true, data: "uploaded" });
    });
  });
});
