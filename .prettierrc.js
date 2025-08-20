module.exports = {
  // Core formatting options
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: "as-needed",
  trailingComma: "es5",
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: "avoid",

  // Language-specific formatting
  overrides: [
    {
      files: "*.json",
      options: {
        printWidth: 120,
        tabWidth: 2,
      },
    },
    {
      files: "*.md",
      options: {
        printWidth: 100,
        proseWrap: "always",
      },
    },
    {
      files: "*.{yml,yaml}",
      options: {
        tabWidth: 2,
        singleQuote: false,
      },
    },
    {
      files: "*.{js,jsx,ts,tsx}",
      options: {
        singleQuote: true,
        jsxSingleQuote: true,
      },
    },
  ],

  // Plugin configurations
  plugins: [
    "@trivago/prettier-plugin-sort-imports",
    "prettier-plugin-tailwindcss",
  ],

  // Import sorting configuration
  importOrder: [
    "^react$",
    "^next",
    "<THIRD_PARTY_MODULES>",
    "^@/(.*)$",
    "^[./]",
  ],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,

  // Tailwind CSS class sorting
  tailwindConfig: "./apps/web/tailwind.config.js",
  tailwindFunctions: ["clsx", "cn", "cva"],
};
