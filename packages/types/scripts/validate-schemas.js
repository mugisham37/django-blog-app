#!/usr/bin/env node

/**
 * Schema validation script
 */

const fs = require("fs");
const path = require("path");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

// Configuration
const CONFIG = {
  schemasPath: "./schemas",
  testDataPath: "./test-data",
  outputPath: "./validation-results",
};

/**
 * Load all JSON schemas
 */
function loadSchemas() {
  const schemasDir = CONFIG.schemasPath;
  const schemas = {};

  if (!fs.existsSync(schemasDir)) {
    console.log("Schemas directory not found:", schemasDir);
    return schemas;
  }

  const files = fs.readdirSync(schemasDir);

  files.forEach((file) => {
    if (file.endsWith(".json")) {
      const filePath = path.join(schemasDir, file);
      try {
        const schema = JSON.parse(fs.readFileSync(filePath, "utf8"));
        const schemaName = path.basename(file, ".json");
        schemas[schemaName] = schema;
        console.log(`✓ Loaded schema: ${schemaName}`);
      } catch (error) {
        console.error(`❌ Failed to load schema ${file}:`, error.message);
      }
    }
  });

  return schemas;
}

/**
 * Load test data
 */
function loadTestData() {
  const testDataDir = CONFIG.testDataPath;
  const testData = {};

  if (!fs.existsSync(testDataDir)) {
    console.log("Test data directory not found:", testDataDir);
    return testData;
  }

  const files = fs.readdirSync(testDataDir);

  files.forEach((file) => {
    if (file.endsWith(".json")) {
      const filePath = path.join(testDataDir, file);
      try {
        const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
        const dataName = path.basename(file, ".json");
        testData[dataName] = data;
        console.log(`✓ Loaded test data: ${dataName}`);
      } catch (error) {
        console.error(`❌ Failed to load test data ${file}:`, error.message);
      }
    }
  });

  return testData;
}

/**
 * Validate schemas themselves
 */
function validateSchemas(schemas) {
  console.log("\n📋 Validating schemas...");

  const ajv = new Ajv({ strict: false });
  addFormats(ajv);

  const results = {
    valid: [],
    invalid: [],
  };

  Object.entries(schemas).forEach(([name, schema]) => {
    try {
      ajv.compile(schema);
      results.valid.push(name);
      console.log(`✓ Schema ${name} is valid`);
    } catch (error) {
      results.invalid.push({ name, error: error.message });
      console.error(`❌ Schema ${name} is invalid:`, error.message);
    }
  });

  return results;
}

/**
 * Validate test data against schemas
 */
function validateTestData(schemas, testData) {
  console.log("\n🧪 Validating test data...");

  const ajv = new Ajv({ allErrors: true });
  addFormats(ajv);

  const results = {
    passed: [],
    failed: [],
  };

  // Compile all schemas
  const compiledSchemas = {};
  Object.entries(schemas).forEach(([name, schema]) => {
    try {
      compiledSchemas[name] = ajv.compile(schema);
    } catch (error) {
      console.error(`❌ Failed to compile schema ${name}:`, error.message);
    }
  });

  // Validate test data
  Object.entries(testData).forEach(([dataName, data]) => {
    // Try to find matching schema
    const schemaName = dataName.replace("-test", "").replace("-sample", "");
    const validator = compiledSchemas[schemaName];

    if (!validator) {
      console.log(`⚠️  No schema found for test data: ${dataName}`);
      return;
    }

    const isValid = validator(data);

    if (isValid) {
      results.passed.push({ dataName, schemaName });
      console.log(`✓ Test data ${dataName} validates against ${schemaName}`);
    } else {
      const errors =
        validator.errors?.map((error) => ({
          path: error.instancePath || error.schemaPath,
          message: error.message,
          value: error.data,
        })) || [];

      results.failed.push({ dataName, schemaName, errors });
      console.error(
        `❌ Test data ${dataName} failed validation against ${schemaName}:`
      );
      errors.forEach((error) => {
        console.error(`  - ${error.path}: ${error.message}`);
      });
    }
  });

  return results;
}

/**
 * Generate sample data from schemas
 */
function generateSampleData(schemas) {
  console.log("\n🎲 Generating sample data...");

  const samples = {};

  Object.entries(schemas).forEach(([name, schema]) => {
    try {
      const sample = generateSampleFromSchema(schema);
      samples[name] = sample;
      console.log(`✓ Generated sample for ${name}`);
    } catch (error) {
      console.error(`❌ Failed to generate sample for ${name}:`, error.message);
    }
  });

  return samples;
}

/**
 * Generate sample data from a single schema
 */
function generateSampleFromSchema(schema) {
  if (schema.type === "object" && schema.properties) {
    const sample = {};

    Object.entries(schema.properties).forEach(([key, prop]) => {
      if (schema.required && schema.required.includes(key)) {
        sample[key] = generateSampleValue(prop);
      }
    });

    return sample;
  }

  return generateSampleValue(schema);
}

/**
 * Generate sample value based on property definition
 */
function generateSampleValue(prop) {
  if (prop.enum) {
    return prop.enum[0];
  }

  switch (prop.type) {
    case "string":
      if (prop.format === "email") return "user@example.com";
      if (prop.format === "date-time") return new Date().toISOString();
      if (prop.format === "date") return new Date().toISOString().split("T")[0];
      if (prop.format === "uri") return "https://example.com";
      if (prop.format === "uuid") return "123e4567-e89b-12d3-a456-426614174000";
      return prop.maxLength
        ? "sample".padEnd(Math.min(prop.maxLength, 10), "x")
        : "sample";

    case "number":
    case "integer":
      return prop.minimum || 1;

    case "boolean":
      return true;

    case "array":
      return prop.items ? [generateSampleValue(prop.items)] : [];

    case "object":
      return {};

    default:
      return null;
  }
}

/**
 * Save validation results
 */
function saveResults(schemaValidation, dataValidation, samples) {
  if (!fs.existsSync(CONFIG.outputPath)) {
    fs.mkdirSync(CONFIG.outputPath, { recursive: true });
  }

  const report = {
    timestamp: new Date().toISOString(),
    schema_validation: schemaValidation,
    data_validation: dataValidation,
    summary: {
      schemas_valid: schemaValidation.valid.length,
      schemas_invalid: schemaValidation.invalid.length,
      tests_passed: dataValidation.passed.length,
      tests_failed: dataValidation.failed.length,
    },
  };

  // Save validation report
  fs.writeFileSync(
    path.join(CONFIG.outputPath, "validation-report.json"),
    JSON.stringify(report, null, 2)
  );

  // Save sample data
  fs.writeFileSync(
    path.join(CONFIG.outputPath, "sample-data.json"),
    JSON.stringify(samples, null, 2)
  );

  console.log(`\n📊 Results saved to ${CONFIG.outputPath}`);
}

/**
 * Print summary
 */
function printSummary(schemaValidation, dataValidation) {
  console.log("\n📈 Validation Summary:");
  console.log(`  Schemas valid: ${schemaValidation.valid.length}`);
  console.log(`  Schemas invalid: ${schemaValidation.invalid.length}`);
  console.log(`  Tests passed: ${dataValidation.passed.length}`);
  console.log(`  Tests failed: ${dataValidation.failed.length}`);

  const totalSchemas =
    schemaValidation.valid.length + schemaValidation.invalid.length;
  const totalTests =
    dataValidation.passed.length + dataValidation.failed.length;

  if (totalSchemas > 0) {
    const schemaSuccessRate = (
      (schemaValidation.valid.length / totalSchemas) *
      100
    ).toFixed(1);
    console.log(`  Schema success rate: ${schemaSuccessRate}%`);
  }

  if (totalTests > 0) {
    const testSuccessRate = (
      (dataValidation.passed.length / totalTests) *
      100
    ).toFixed(1);
    console.log(`  Test success rate: ${testSuccessRate}%`);
  }
}

/**
 * Main execution function
 */
function main() {
  console.log("🔍 Starting schema validation...");

  try {
    // Load schemas and test data
    const schemas = loadSchemas();
    const testData = loadTestData();

    if (Object.keys(schemas).length === 0) {
      console.log("⚠️  No schemas found to validate");
      return;
    }

    // Validate schemas
    const schemaValidation = validateSchemas(schemas);

    // Validate test data
    const dataValidation = validateTestData(schemas, testData);

    // Generate sample data
    const samples = generateSampleData(schemas);

    // Save results
    saveResults(schemaValidation, dataValidation, samples);

    // Print summary
    printSummary(schemaValidation, dataValidation);

    console.log("\n✅ Schema validation completed!");
  } catch (error) {
    console.error("❌ Schema validation failed:", error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  loadSchemas,
  loadTestData,
  validateSchemas,
  validateTestData,
  generateSampleData,
};
