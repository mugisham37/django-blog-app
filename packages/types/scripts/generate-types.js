#!/usr/bin/env node

/**
 * Type generation script for Django models to TypeScript interfaces
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Configuration
const CONFIG = {
  djangoProjectPath: "../../apps/api",
  outputPath: "./src/generated",
  pythonTypesPath: "./python/generated",
  schemaOutputPath: "./schemas/generated",
};

// Django field type mappings to TypeScript
const DJANGO_TO_TS_MAPPING = {
  AutoField: "number",
  BigAutoField: "number",
  BigIntegerField: "number",
  BooleanField: "boolean",
  CharField: "string",
  DateField: "string",
  DateTimeField: "string",
  DecimalField: "number",
  EmailField: "string",
  FileField: "string",
  FloatField: "number",
  ImageField: "string",
  IntegerField: "number",
  JSONField: "Record<string, unknown>",
  PositiveIntegerField: "number",
  PositiveSmallIntegerField: "number",
  SlugField: "string",
  SmallIntegerField: "number",
  TextField: "string",
  TimeField: "string",
  URLField: "string",
  UUIDField: "string",
  ForeignKey: "number",
  OneToOneField: "number",
  ManyToManyField: "number[]",
};

// Django field type mappings to Python types
const DJANGO_TO_PYTHON_MAPPING = {
  AutoField: "int",
  BigAutoField: "int",
  BigIntegerField: "int",
  BooleanField: "bool",
  CharField: "str",
  DateField: "datetime.date",
  DateTimeField: "datetime.datetime",
  DecimalField: "decimal.Decimal",
  EmailField: "str",
  FileField: "str",
  FloatField: "float",
  ImageField: "str",
  IntegerField: "int",
  JSONField: "Dict[str, Any]",
  PositiveIntegerField: "int",
  PositiveSmallIntegerField: "int",
  SlugField: "str",
  SmallIntegerField: "int",
  TextField: "str",
  TimeField: "datetime.time",
  URLField: "str",
  UUIDField: "str",
  ForeignKey: "int",
  OneToOneField: "int",
  ManyToManyField: "List[int]",
};

/**
 * Extract Django model information
 */
function extractDjangoModels() {
  console.log("Extracting Django models...");

  try {
    // Run Django management command to extract model information
    const command = `cd ${CONFIG.djangoProjectPath} && python manage.py shell -c "
import json
from django.apps import apps
from django.db import models

model_info = {}
for model in apps.get_models():
    app_label = model._meta.app_label
    model_name = model.__name__
    
    if app_label not in model_info:
        model_info[app_label] = {}
    
    fields = {}
    for field in model._meta.get_fields():
        field_info = {
            'type': field.__class__.__name__,
            'null': getattr(field, 'null', False),
            'blank': getattr(field, 'blank', False),
            'max_length': getattr(field, 'max_length', None),
            'choices': getattr(field, 'choices', None),
            'default': str(getattr(field, 'default', None)) if hasattr(field, 'default') else None,
        }
        
        if hasattr(field, 'related_model') and field.related_model:
            field_info['related_model'] = field.related_model.__name__
            field_info['related_app'] = field.related_model._meta.app_label
        
        fields[field.name] = field_info
    
    model_info[app_label][model_name] = {
        'fields': fields,
        'verbose_name': model._meta.verbose_name,
        'verbose_name_plural': model._meta.verbose_name_plural,
    }

print(json.dumps(model_info, indent=2))
"`;

    const output = execSync(command, { encoding: "utf8" });
    return JSON.parse(output);
  } catch (error) {
    console.error("Error extracting Django models:", error.message);
    return {};
  }
}

/**
 * Generate TypeScript interfaces from Django models
 */
function generateTypeScriptInterfaces(modelInfo) {
  console.log("Generating TypeScript interfaces...");

  const interfaces = [];

  for (const [appLabel, models] of Object.entries(modelInfo)) {
    for (const [modelName, modelData] of Object.entries(models)) {
      const interfaceName = modelName;
      const fields = [];

      for (const [fieldName, fieldInfo] of Object.entries(modelData.fields)) {
        let tsType = DJANGO_TO_TS_MAPPING[fieldInfo.type] || "unknown";

        // Handle nullable fields
        if (fieldInfo.null || fieldInfo.blank) {
          tsType += " | null";
        }

        // Handle choices
        if (fieldInfo.choices) {
          const choiceValues = fieldInfo.choices
            .map((choice) => `'${choice[0]}'`)
            .join(" | ");
          tsType = choiceValues;
        }

        // Handle related models
        if (fieldInfo.related_model) {
          if (fieldInfo.type === "ManyToManyField") {
            tsType = `${fieldInfo.related_model}[]`;
          } else {
            tsType = fieldInfo.related_model;
          }
        }

        const optional =
          fieldInfo.null || fieldInfo.blank || fieldInfo.default !== null
            ? "?"
            : "";
        fields.push(`  readonly ${fieldName}${optional}: ${tsType};`);
      }

      const interfaceCode = `
/**
 * ${modelData.verbose_name} interface
 * Generated from Django model: ${appLabel}.${modelName}
 */
export interface ${interfaceName} {
${fields.join("\n")}
}`;

      interfaces.push(interfaceCode);
    }
  }

  return interfaces.join("\n\n");
}

/**
 * Generate Python dataclasses from Django models
 */
function generatePythonDataclasses(modelInfo) {
  console.log("Generating Python dataclasses...");

  const imports = [
    "from dataclasses import dataclass",
    "from typing import Optional, List, Dict, Any",
    "from datetime import datetime, date, time",
    "from decimal import Decimal",
  ];

  const dataclasses = [];

  for (const [appLabel, models] of Object.entries(modelInfo)) {
    for (const [modelName, modelData] of Object.entries(models)) {
      const className = modelName;
      const fields = [];

      for (const [fieldName, fieldInfo] of Object.entries(modelData.fields)) {
        let pythonType = DJANGO_TO_PYTHON_MAPPING[fieldInfo.type] || "Any";

        // Handle nullable fields
        if (fieldInfo.null || fieldInfo.blank) {
          pythonType = `Optional[${pythonType}]`;
        }

        // Handle related models
        if (fieldInfo.related_model) {
          if (fieldInfo.type === "ManyToManyField") {
            pythonType = `List[${fieldInfo.related_model}]`;
          } else {
            pythonType = fieldInfo.related_model;
          }
        }

        const defaultValue =
          fieldInfo.default !== null
            ? ` = ${fieldInfo.default}`
            : fieldInfo.null || fieldInfo.blank
            ? " = None"
            : "";

        fields.push(`    ${fieldName}: ${pythonType}${defaultValue}`);
      }

      const dataclassCode = `
@dataclass
class ${className}:
    """
    ${modelData.verbose_name}
    Generated from Django model: ${appLabel}.${modelName}
    """
${fields.join("\n")}`;

      dataclasses.push(dataclassCode);
    }
  }

  return imports.join("\n") + "\n\n" + dataclasses.join("\n\n");
}

/**
 * Generate JSON schemas from Django models
 */
function generateJSONSchemas(modelInfo) {
  console.log("Generating JSON schemas...");

  const schemas = {};

  for (const [appLabel, models] of Object.entries(modelInfo)) {
    for (const [modelName, modelData] of Object.entries(models)) {
      const properties = {};
      const required = [];

      for (const [fieldName, fieldInfo] of Object.entries(modelData.fields)) {
        let jsonType = "string";
        const property = {};

        // Map Django field types to JSON schema types
        switch (fieldInfo.type) {
          case "BooleanField":
            jsonType = "boolean";
            break;
          case "IntegerField":
          case "BigIntegerField":
          case "AutoField":
          case "BigAutoField":
          case "PositiveIntegerField":
          case "PositiveSmallIntegerField":
          case "SmallIntegerField":
            jsonType = "integer";
            break;
          case "FloatField":
          case "DecimalField":
            jsonType = "number";
            break;
          case "DateTimeField":
            jsonType = "string";
            property.format = "date-time";
            break;
          case "DateField":
            jsonType = "string";
            property.format = "date";
            break;
          case "TimeField":
            jsonType = "string";
            property.format = "time";
            break;
          case "EmailField":
            jsonType = "string";
            property.format = "email";
            break;
          case "URLField":
            jsonType = "string";
            property.format = "uri";
            break;
          case "UUIDField":
            jsonType = "string";
            property.format = "uuid";
            break;
          case "JSONField":
            jsonType = "object";
            break;
          case "ManyToManyField":
            jsonType = "array";
            property.items = { type: "integer" };
            break;
        }

        property.type = jsonType;

        // Add constraints
        if (fieldInfo.max_length) {
          property.maxLength = fieldInfo.max_length;
        }

        if (fieldInfo.choices) {
          property.enum = fieldInfo.choices.map((choice) => choice[0]);
        }

        properties[fieldName] = property;

        // Add to required if not nullable and no default
        if (!fieldInfo.null && !fieldInfo.blank && fieldInfo.default === null) {
          required.push(fieldName);
        }
      }

      schemas[`${appLabel}_${modelName}`] = {
        type: "object",
        title: modelData.verbose_name,
        description: `Schema for ${appLabel}.${modelName}`,
        properties,
        required,
      };
    }
  }

  return JSON.stringify(schemas, null, 2);
}

/**
 * Ensure output directories exist
 */
function ensureDirectories() {
  const dirs = [
    CONFIG.outputPath,
    CONFIG.pythonTypesPath,
    CONFIG.schemaOutputPath,
  ];

  dirs.forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

/**
 * Main execution function
 */
function main() {
  console.log("Starting type generation...");

  try {
    // Ensure output directories exist
    ensureDirectories();

    // Extract Django model information
    const modelInfo = extractDjangoModels();

    if (Object.keys(modelInfo).length === 0) {
      console.log("No Django models found or extraction failed.");
      return;
    }

    // Generate TypeScript interfaces
    const tsInterfaces = generateTypeScriptInterfaces(modelInfo);
    fs.writeFileSync(
      path.join(CONFIG.outputPath, "django-models.ts"),
      tsInterfaces
    );
    console.log("✓ TypeScript interfaces generated");

    // Generate Python dataclasses
    const pythonDataclasses = generatePythonDataclasses(modelInfo);
    fs.writeFileSync(
      path.join(CONFIG.pythonTypesPath, "django_models.py"),
      pythonDataclasses
    );
    console.log("✓ Python dataclasses generated");

    // Generate JSON schemas
    const jsonSchemas = generateJSONSchemas(modelInfo);
    fs.writeFileSync(
      path.join(CONFIG.schemaOutputPath, "django-models.json"),
      jsonSchemas
    );
    console.log("✓ JSON schemas generated");

    // Generate index file for TypeScript
    const indexContent = `
// Auto-generated Django model types
export * from './django-models';

// Re-export common types
export * from '../index';
`;
    fs.writeFileSync(path.join(CONFIG.outputPath, "index.ts"), indexContent);

    console.log("✅ Type generation completed successfully!");
  } catch (error) {
    console.error("❌ Type generation failed:", error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  extractDjangoModels,
  generateTypeScriptInterfaces,
  generatePythonDataclasses,
  generateJSONSchemas,
};
