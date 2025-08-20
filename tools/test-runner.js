#!/usr/bin/env node
/**
 * Comprehensive test runner for the entire project
 * Orchestrates all types of testing across the monorepo
 */

const { execSync, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const chalk = require("chalk");

class TestRunner {
  constructor() {
    this.results = {
      unit: { passed: false, duration: 0 },
      integration: { passed: false, duration: 0 },
      e2e: { passed: false, duration: 0 },
      api: { passed: false, duration: 0 },
      performance: { passed: false, duration: 0 },
      coverage: { passed: false, threshold: 80 },
    };

    this.config = {
      parallel: process.argv.includes("--parallel"),
      verbose: process.argv.includes("--verbose"),
      coverage: !process.argv.includes("--no-coverage"),
      suite: this.getSuiteFromArgs(),
      environment: process.env.NODE_ENV || "test",
    };
  }

  getSuiteFromArgs() {
    const suiteArg = process.argv.find((arg) => arg.startsWith("--suite="));
    return suiteArg ? suiteArg.split("=")[1] : "all";
  }

  async run() {
    console.log(chalk.blue.bold("🚀 Starting Enterprise Blog Test Suite"));
    console.log(chalk.gray(`Environment: ${this.config.environment}`));
    console.log(chalk.gray(`Suite: ${this.config.suite}`));
    console.log(
      chalk.gray(`Coverage: ${this.config.coverage ? "enabled" : "disabled"}`)
    );
    console.log("");

    const startTime = Date.now();

    try {
      // Setup test environment
      await this.setupEnvironment();

      // Run test suites based on configuration
      if (this.config.suite === "all" || this.config.suite === "unit") {
        await this.runUnitTests();
      }

      if (this.config.suite === "all" || this.config.suite === "integration") {
        await this.runIntegrationTests();
      }

      if (this.config.suite === "all" || this.config.suite === "api") {
        await this.runApiTests();
      }

      if (this.config.suite === "all" || this.config.suite === "e2e") {
        await this.runE2ETests();
      }

      if (this.config.suite === "all" || this.config.suite === "performance") {
        await this.runPerformanceTests();
      }

      // Generate coverage report
      if (this.config.coverage) {
        await this.generateCoverageReport();
      }

      // Generate final report
      const totalDuration = Date.now() - startTime;
      this.generateFinalReport(totalDuration);
    } catch (error) {
      console.error(chalk.red.bold("❌ Test suite failed:"), error.message);
      process.exit(1);
    } finally {
      await this.cleanup();
    }
  }

  async setupEnvironment() {
    console.log(chalk.yellow("⚙️ Setting up test environment..."));

    // Ensure test directories exist
    const testDirs = ["tests/reports", "tests/coverage", "tests/artifacts"];

    testDirs.forEach((dir) => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });

    // Install dependencies if needed
    if (!fs.existsSync("node_modules")) {
      console.log(chalk.yellow("📦 Installing dependencies..."));
      execSync("npm install", { stdio: "inherit" });
    }

    // Setup Python virtual environment for Django tests
    if (!fs.existsSync("venv")) {
      console.log(chalk.yellow("🐍 Setting up Python virtual environment..."));
      execSync("python -m venv venv", { stdio: "inherit" });
    }

    // Install Python test dependencies
    console.log(chalk.yellow("📦 Installing Python test dependencies..."));
    execSync("venv/Scripts/pip install -r tests/requirements.txt", {
      stdio: "inherit",
    });

    console.log(chalk.green("✅ Environment setup complete"));
  }

  async runUnitTests() {
    console.log(chalk.blue("\n🧪 Running Unit Tests..."));
    const startTime = Date.now();

    try {
      // Run Django unit tests
      console.log(chalk.gray("Running Django unit tests..."));
      execSync("venv/Scripts/python -m pytest tests/django/ -v --tb=short", {
        stdio: this.config.verbose ? "inherit" : "pipe",
        cwd: process.cwd(),
      });

      // Run JavaScript/TypeScript unit tests
      console.log(chalk.gray("Running JavaScript/TypeScript unit tests..."));
      execSync("npm run test:unit", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      // Run package tests
      console.log(chalk.gray("Running package tests..."));
      execSync("npm run test:packages", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      this.results.unit.passed = true;
      this.results.unit.duration = Date.now() - startTime;
      console.log(chalk.green("✅ Unit tests passed"));
    } catch (error) {
      this.results.unit.duration = Date.now() - startTime;
      console.log(chalk.red("❌ Unit tests failed"));
      throw error;
    }
  }

  async runIntegrationTests() {
    console.log(chalk.blue("\n🔗 Running Integration Tests..."));
    const startTime = Date.now();

    try {
      // Run Django integration tests
      console.log(chalk.gray("Running Django integration tests..."));
      execSync(
        "venv/Scripts/python -m pytest tests/django/ -m integration -v",
        {
          stdio: this.config.verbose ? "inherit" : "pipe",
        }
      );

      // Run frontend integration tests
      console.log(chalk.gray("Running frontend integration tests..."));
      execSync("npm run test:integration", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      this.results.integration.passed = true;
      this.results.integration.duration = Date.now() - startTime;
      console.log(chalk.green("✅ Integration tests passed"));
    } catch (error) {
      this.results.integration.duration = Date.now() - startTime;
      console.log(chalk.red("❌ Integration tests failed"));
      throw error;
    }
  }

  async runApiTests() {
    console.log(chalk.blue("\n🌐 Running API Tests..."));
    const startTime = Date.now();

    try {
      // Check if Newman is installed
      try {
        execSync("newman --version", { stdio: "pipe" });
      } catch {
        console.log(chalk.yellow("Installing Newman..."));
        execSync("npm install -g newman", { stdio: "inherit" });
      }

      // Run Postman collection with Newman
      console.log(chalk.gray("Running Postman API tests..."));
      execSync(
        `newman run tests/api/postman-collection.json -e tests/api/environments/development.json --reporters cli,json --reporter-json-export tests/reports/api-results.json`,
        {
          stdio: this.config.verbose ? "inherit" : "pipe",
        }
      );

      this.results.api.passed = true;
      this.results.api.duration = Date.now() - startTime;
      console.log(chalk.green("✅ API tests passed"));
    } catch (error) {
      this.results.api.duration = Date.now() - startTime;
      console.log(chalk.red("❌ API tests failed"));
      throw error;
    }
  }

  async runE2ETests() {
    console.log(chalk.blue("\n🎭 Running E2E Tests..."));
    const startTime = Date.now();

    try {
      // Install Playwright browsers if needed
      console.log(chalk.gray("Ensuring Playwright browsers are installed..."));
      execSync("npx playwright install", { stdio: "pipe" });

      // Run Playwright tests
      console.log(chalk.gray("Running Playwright E2E tests..."));
      execSync("npx playwright test --config=tests/playwright.config.ts", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      this.results.e2e.passed = true;
      this.results.e2e.duration = Date.now() - startTime;
      console.log(chalk.green("✅ E2E tests passed"));
    } catch (error) {
      this.results.e2e.duration = Date.now() - startTime;
      console.log(chalk.red("❌ E2E tests failed"));
      throw error;
    }
  }

  async runPerformanceTests() {
    console.log(chalk.blue("\n⚡ Running Performance Tests..."));
    const startTime = Date.now();

    try {
      // Check if k6 is installed
      try {
        execSync("k6 version", { stdio: "pipe" });
      } catch {
        console.log(
          chalk.yellow(
            "k6 not found. Please install k6 to run performance tests."
          )
        );
        console.log(
          chalk.gray("Visit: https://k6.io/docs/getting-started/installation/")
        );
        return;
      }

      // Run load tests
      console.log(chalk.gray("Running load tests..."));
      execSync("k6 run tests/performance/load-test.js", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      this.results.performance.passed = true;
      this.results.performance.duration = Date.now() - startTime;
      console.log(chalk.green("✅ Performance tests passed"));
    } catch (error) {
      this.results.performance.duration = Date.now() - startTime;
      console.log(chalk.red("❌ Performance tests failed"));
      // Don't throw for performance tests in development
      if (this.config.environment === "ci") {
        throw error;
      }
    }
  }

  async generateCoverageReport() {
    console.log(chalk.blue("\n📊 Generating Coverage Report..."));

    try {
      // Merge coverage reports from different test suites
      console.log(chalk.gray("Merging coverage reports..."));

      // Generate combined HTML report
      execSync("npm run coverage:report", {
        stdio: this.config.verbose ? "inherit" : "pipe",
      });

      // Check coverage thresholds
      const coverageData = this.parseCoverageData();
      const meetsThreshold =
        coverageData.total >= this.results.coverage.threshold;

      this.results.coverage.passed = meetsThreshold;

      if (meetsThreshold) {
        console.log(
          chalk.green(`✅ Coverage threshold met: ${coverageData.total}%`)
        );
      } else {
        console.log(
          chalk.red(
            `❌ Coverage below threshold: ${coverageData.total}% < ${this.results.coverage.threshold}%`
          )
        );
      }
    } catch (error) {
      console.log(chalk.red("❌ Coverage report generation failed"));
      if (this.config.environment === "ci") {
        throw error;
      }
    }
  }

  parseCoverageData() {
    try {
      const coveragePath = "tests/coverage/coverage-summary.json";
      if (fs.existsSync(coveragePath)) {
        const coverage = JSON.parse(fs.readFileSync(coveragePath, "utf8"));
        return {
          total: Math.round(coverage.total.lines.pct),
          lines: Math.round(coverage.total.lines.pct),
          functions: Math.round(coverage.total.functions.pct),
          branches: Math.round(coverage.total.branches.pct),
          statements: Math.round(coverage.total.statements.pct),
        };
      }
    } catch (error) {
      console.log(chalk.yellow("⚠️ Could not parse coverage data"));
    }

    return { total: 0, lines: 0, functions: 0, branches: 0, statements: 0 };
  }

  generateFinalReport(totalDuration) {
    console.log(chalk.blue.bold("\n📋 Test Suite Summary"));
    console.log(chalk.gray("=".repeat(50)));

    const formatDuration = (ms) => `${(ms / 1000).toFixed(2)}s`;
    const formatResult = (result) =>
      result.passed ? chalk.green("✅ PASS") : chalk.red("❌ FAIL");

    console.log(
      `Unit Tests:        ${formatResult(this.results.unit)} (${formatDuration(
        this.results.unit.duration
      )})`
    );
    console.log(
      `Integration Tests: ${formatResult(
        this.results.integration
      )} (${formatDuration(this.results.integration.duration)})`
    );
    console.log(
      `API Tests:         ${formatResult(this.results.api)} (${formatDuration(
        this.results.api.duration
      )})`
    );
    console.log(
      `E2E Tests:         ${formatResult(this.results.e2e)} (${formatDuration(
        this.results.e2e.duration
      )})`
    );
    console.log(
      `Performance Tests: ${formatResult(
        this.results.performance
      )} (${formatDuration(this.results.performance.duration)})`
    );

    if (this.config.coverage) {
      console.log(`Coverage:          ${formatResult(this.results.coverage)}`);
    }

    console.log(chalk.gray("=".repeat(50)));
    console.log(`Total Duration:    ${formatDuration(totalDuration)}`);

    const allPassed = Object.values(this.results).every(
      (result) => result.passed
    );

    if (allPassed) {
      console.log(chalk.green.bold("\n🎉 All tests passed!"));
    } else {
      console.log(chalk.red.bold("\n💥 Some tests failed!"));
      process.exit(1);
    }

    // Generate JSON report for CI
    const report = {
      timestamp: new Date().toISOString(),
      environment: this.config.environment,
      suite: this.config.suite,
      duration: totalDuration,
      results: this.results,
      passed: allPassed,
    };

    fs.writeFileSync(
      "tests/reports/test-summary.json",
      JSON.stringify(report, null, 2)
    );
    console.log(
      chalk.gray(
        "\n📄 Detailed report saved to tests/reports/test-summary.json"
      )
    );
  }

  async cleanup() {
    console.log(chalk.yellow("\n🧹 Cleaning up..."));

    // Clean up temporary test files
    const tempFiles = ["tests/e2e/auth-state.json", ".nyc_output"];

    tempFiles.forEach((file) => {
      if (fs.existsSync(file)) {
        fs.rmSync(file, { recursive: true, force: true });
      }
    });

    console.log(chalk.green("✅ Cleanup complete"));
  }
}

// CLI usage
if (require.main === module) {
  const runner = new TestRunner();
  runner.run().catch((error) => {
    console.error(chalk.red.bold("Fatal error:"), error);
    process.exit(1);
  });
}

module.exports = TestRunner;
