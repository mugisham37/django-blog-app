module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
    jest: true,
  },
  extends: [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "@typescript-eslint/recommended-requiring-type-checking",
    "next/core-web-vitals",
    "prettier",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
    project: [
      "./tsconfig.json",
      "./apps/*/tsconfig.json",
      "./packages/*/tsconfig.json",
      "./tests/tsconfig.json",
    ],
  },
  plugins: [
    "@typescript-eslint",
    "react",
    "react-hooks",
    "jsx-a11y",
    "import",
    "security",
    "sonarjs",
  ],
  rules: {
    // TypeScript specific rules
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-return": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "@typescript-eslint/strict-boolean-expressions": "error",
    "@typescript-eslint/switch-exhaustiveness-check": "error",

    // Import rules
    "import/order": [
      "error",
      {
        groups: [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index",
        ],
        "newlines-between": "always",
        alphabetize: {
          order: "asc",
          caseInsensitive: true,
        },
      },
    ],
    "import/no-duplicates": "error",
    "import/no-unused-modules": "error",

    // React rules
    "react/jsx-uses-react": "off",
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "react/jsx-props-no-spreading": "warn",
    "react/jsx-key": "error",
    "react/no-array-index-key": "warn",
    "react/no-danger": "error",
    "react/no-deprecated": "error",
    "react/no-unsafe": "error",

    // React Hooks rules
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",

    // Accessibility rules
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/anchor-has-content": "error",
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/heading-has-content": "error",
    "jsx-a11y/img-redundant-alt": "error",
    "jsx-a11y/no-access-key": "error",

    // Security rules
    "security/detect-object-injection": "error",
    "security/detect-non-literal-regexp": "error",
    "security/detect-unsafe-regex": "error",
    "security/detect-buffer-noassert": "error",
    "security/detect-child-process": "error",
    "security/detect-disable-mustache-escape": "error",
    "security/detect-eval-with-expression": "error",
    "security/detect-no-csrf-before-method-override": "error",
    "security/detect-non-literal-fs-filename": "error",
    "security/detect-non-literal-require": "error",
    "security/detect-possible-timing-attacks": "error",
    "security/detect-pseudoRandomBytes": "error",

    // SonarJS rules for code quality
    "sonarjs/cognitive-complexity": ["error", 15],
    "sonarjs/max-switch-cases": ["error", 30],
    "sonarjs/no-all-duplicated-branches": "error",
    "sonarjs/no-collapsible-if": "error",
    "sonarjs/no-collection-size-mischeck": "error",
    "sonarjs/no-duplicate-string": ["error", 3],
    "sonarjs/no-duplicated-branches": "error",
    "sonarjs/no-element-overwrite": "error",
    "sonarjs/no-empty-collection": "error",
    "sonarjs/no-extra-arguments": "error",
    "sonarjs/no-identical-conditions": "error",
    "sonarjs/no-identical-expressions": "error",
    "sonarjs/no-ignored-return": "error",
    "sonarjs/no-inverted-boolean-check": "error",
    "sonarjs/no-one-iteration-loop": "error",
    "sonarjs/no-redundant-boolean": "error",
    "sonarjs/no-redundant-jump": "error",
    "sonarjs/no-same-line-conditional": "error",
    "sonarjs/no-small-switch": "error",
    "sonarjs/no-unused-collection": "error",
    "sonarjs/no-use-of-empty-return-value": "error",
    "sonarjs/no-useless-catch": "error",
    "sonarjs/prefer-immediate-return": "error",
    "sonarjs/prefer-object-literal": "error",
    "sonarjs/prefer-single-boolean-return": "error",
    "sonarjs/prefer-while": "error",

    // General code quality rules
    "no-console": "warn",
    "no-debugger": "error",
    "no-alert": "error",
    "no-var": "error",
    "prefer-const": "error",
    "prefer-arrow-callback": "error",
    "arrow-body-style": ["error", "as-needed"],
    "object-shorthand": "error",
    "prefer-template": "error",
    "template-curly-spacing": "error",
    "no-useless-concat": "error",
    "no-useless-return": "error",
    "no-unreachable": "error",
    "no-duplicate-imports": "error",
    "no-magic-numbers": ["warn", { ignore: [-1, 0, 1, 2] }],
    complexity: ["error", 10],
    "max-depth": ["error", 4],
    "max-lines": ["error", 500],
    "max-lines-per-function": ["error", 50],
    "max-params": ["error", 4],
  },
  overrides: [
    {
      files: ["**/*.test.{js,jsx,ts,tsx}", "**/*.spec.{js,jsx,ts,tsx}"],
      env: {
        jest: true,
      },
      rules: {
        "no-magic-numbers": "off",
        "@typescript-eslint/no-unsafe-assignment": "off",
        "@typescript-eslint/no-unsafe-member-access": "off",
        "sonarjs/no-duplicate-string": "off",
      },
    },
    {
      files: ["**/*.config.{js,ts}", "**/next.config.{js,ts}"],
      rules: {
        "import/no-anonymous-default-export": "off",
        "@typescript-eslint/no-var-requires": "off",
      },
    },
    {
      files: ["apps/web/**/*"],
      extends: ["next/core-web-vitals"],
      rules: {
        "@next/next/no-html-link-for-pages": "off",
      },
    },
  ],
  settings: {
    react: {
      version: "detect",
    },
    "import/resolver": {
      typescript: {
        alwaysTryTypes: true,
        project: [
          "./tsconfig.json",
          "./apps/*/tsconfig.json",
          "./packages/*/tsconfig.json",
        ],
      },
    },
  },
};
