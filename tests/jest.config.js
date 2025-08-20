const nextJest = require("next/jest");

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: "../apps/web/",
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/tests/e2e/",
    "<rootDir>/tests/performance/",
  ],
  collectCoverageFrom: [
    "apps/web/**/*.{js,jsx,ts,tsx}",
    "packages/**/*.{js,jsx,ts,tsx}",
    "!**/*.d.ts",
    "!**/node_modules/**",
    "!**/.next/**",
    "!**/coverage/**",
    "!**/*.config.{js,ts}",
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  moduleNameMapping: {
    // Handle module aliases
    "^@/(.*)$": "<rootDir>/apps/web/src/$1",
    "^@packages/(.*)$": "<rootDir>/packages/$1",
    "^@/components/(.*)$": "<rootDir>/apps/web/src/components/$1",
    "^@/pages/(.*)$": "<rootDir>/apps/web/src/pages/$1",
    "^@/lib/(.*)$": "<rootDir>/apps/web/src/lib/$1",
    "^@/hooks/(.*)$": "<rootDir>/apps/web/src/hooks/$1",
    "^@/utils/(.*)$": "<rootDir>/apps/web/src/utils/$1",
    "^@/types/(.*)$": "<rootDir>/packages/types/src/$1",
    "^@/api-client/(.*)$": "<rootDir>/packages/api-client/src/$1",
  },
  testMatch: [
    "<rootDir>/tests/frontend/**/*.test.{js,jsx,ts,tsx}",
    "<rootDir>/tests/packages/**/*.test.{js,jsx,ts,tsx}",
    "<rootDir>/apps/web/**/*.test.{js,jsx,ts,tsx}",
    "<rootDir>/packages/**/*.test.{js,jsx,ts,tsx}",
  ],
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": ["babel-jest", { presets: ["next/babel"] }],
  },
  transformIgnorePatterns: [
    "/node_modules/",
    "^.+\\.module\\.(css|sass|scss)$",
  ],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],
  globals: {
    "ts-jest": {
      tsconfig: {
        jsx: "react-jsx",
      },
    },
  },
  // Test environment setup
  testEnvironmentOptions: {
    url: "http://localhost:3000",
  },
  // Custom test runners for different types
  projects: [
    {
      displayName: "Frontend Components",
      testMatch: [
        "<rootDir>/tests/frontend/components/**/*.test.{js,jsx,ts,tsx}",
      ],
      setupFilesAfterEnv: ["<rootDir>/tests/frontend/setup.js"],
    },
    {
      displayName: "Frontend Pages",
      testMatch: ["<rootDir>/tests/frontend/pages/**/*.test.{js,jsx,ts,tsx}"],
      setupFilesAfterEnv: ["<rootDir>/tests/frontend/setup.js"],
    },
    {
      displayName: "Frontend Hooks",
      testMatch: ["<rootDir>/tests/frontend/hooks/**/*.test.{js,jsx,ts,tsx}"],
      setupFilesAfterEnv: ["<rootDir>/tests/frontend/setup.js"],
    },
    {
      displayName: "API Client",
      testMatch: [
        "<rootDir>/tests/packages/api-client/**/*.test.{js,jsx,ts,tsx}",
      ],
      setupFilesAfterEnv: ["<rootDir>/tests/packages/setup.js"],
    },
    {
      displayName: "Packages",
      testMatch: ["<rootDir>/tests/packages/**/*.test.{js,jsx,ts,tsx}"],
      setupFilesAfterEnv: ["<rootDir>/tests/packages/setup.js"],
    },
  ],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);
