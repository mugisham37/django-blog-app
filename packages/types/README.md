# @enterprise/types

Shared TypeScript and Python type definitions for the enterprise fullstack monolith.

## Overview

This package provides comprehensive type definitions that are shared across the entire application stack, including:

- **TypeScript interfaces** for frontend applications
- **Python dataclasses** for backend services
- **JSON schemas** for API validation
- **Validation utilities** for runtime type checking
- **Type generation scripts** for automatic updates

## Features

### 🎯 Comprehensive Type Coverage

- **Authentication & Authorization**: User roles, permissions, JWT tokens, OAuth2
- **Blog System**: Posts, categories, tags, comments with full metadata
- **User Management**: Profiles, preferences, activities, notifications
- **Analytics**: Events, metrics, reports with detailed tracking
- **Newsletter**: Campaigns, subscribers, templates, automation
- **WebSocket**: Real-time events, connection management, room handling
- **Caching**: Multi-level strategies, providers, invalidation
- **Database**: Connections, transactions, migrations, monitoring
- **API**: Responses, pagination, bulk operations, search

### 🔧 Validation & Safety

- **JSON Schema validation** with AJV
- **Runtime validation** with Zod
- **Type guards** and utility functions
- **File upload validation**
- **Password strength checking**
- **Input sanitization**

### 🚀 Developer Experience

- **Auto-completion** in IDEs
- **Type safety** across the stack
- **Consistent interfaces** between frontend and backend
- **Automatic type generation** from Django models
- **Comprehensive test coverage**

## Installation

```bash
npm install @enterprise/types
```

For Python types:

```bash
pip install -e packages/types
```

## Usage

### TypeScript

```typescript
import {
  User,
  Post,
  APIResponse,
  validateWithSchema,
  ZodSchemas,
} from "@enterprise/types";

// Type-safe API response
const response: APIResponse<User> = {
  success: true,
  data: {
    id: 1,
    username: "john_doe",
    email: "john@example.com",
    role: UserRole.AUTHOR,
    // ... other fields
  },
  message: "User retrieved successfully",
};

// Runtime validation
const loginResult = ZodSchemas.LoginRequest.safeParse({
  email: "user@example.com",
  password: "securepassword",
});

if (loginResult.success) {
  // Type-safe access to validated data
  console.log(loginResult.data.email);
}

// Schema validation
const validationResult = validateWithSchema("UserSchema", userData);
if (validationResult.success) {
  // Data is validated and typed
  const user = validationResult.data;
}
```

### Python

```python
from enterprise_types import (
    User,
    UserRole,
    UserStatus,
    APIResponse,
    ValidationResult
)

# Type-safe data structures
user = User(
    id=1,
    username="john_doe",
    email="john@example.com",
    role=UserRole.AUTHOR,
    status=UserStatus.ACTIVE,
    is_verified=True,
    is_staff=False,
    is_superuser=False,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    permissions=[]
)

# API responses
response = APIResponse.success_response(
    data=user,
    message="User retrieved successfully"
)
```

### Validation

```typescript
import { ValidationUtils } from "@enterprise/types";

// Email validation
if (ValidationUtils.isEmail("user@example.com")) {
  // Valid email
}

// Password strength
const strength = ValidationUtils.validatePasswordStrength("MyP@ssw0rd123");
console.log(`Password score: ${strength.score}/5`);

// File upload validation
const fileResult = ValidationUtils.validateFileUpload(file, {
  maxSize: 5 * 1024 * 1024, // 5MB
  allowedTypes: ["image/jpeg", "image/png"],
});

if (fileResult.success) {
  // File is valid
  uploadFile(fileResult.data);
}
```

## Type Generation

### Automatic Django Model Types

Generate TypeScript interfaces from Django models:

```bash
npm run generate:types
```

This will:

1. Extract model information from Django
2. Generate TypeScript interfaces
3. Create Python dataclasses
4. Generate JSON schemas
5. Update validation rules

### Manual Type Updates

When adding new types:

1. **TypeScript**: Add to appropriate file in `src/`
2. **Python**: Add to corresponding file in `python/`
3. **Schemas**: Update `src/validation/schemas.ts`
4. **Tests**: Add tests in `__tests__/`

## Validation

### Schema Validation

Validate all schemas and test data:

```bash
npm run validate:schemas
```

This will:

- Validate all JSON schemas
- Test schemas against sample data
- Generate validation reports
- Create sample data for testing

### Runtime Validation

```typescript
// Using Zod for runtime validation
const userSchema = ZodSchemas.RegisterRequest;
const result = userSchema.safeParse(formData);

if (!result.success) {
  // Handle validation errors
  result.error.errors.forEach((error) => {
    console.log(`${error.path}: ${error.message}`);
  });
}

// Using AJV for JSON schema validation
const validator = createValidator("UserSchema");
const validation = validator(userData);

if (!validation.success) {
  // Handle validation errors
  validation.errors?.forEach((error) => {
    console.log(`${error.field}: ${error.message}`);
  });
}
```

## Testing

Run the test suite:

```bash
npm test
```

Run tests with coverage:

```bash
npm run test:coverage
```

Watch mode for development:

```bash
npm run test:watch
```

## API Reference

### Core Types

- **BaseEntity**: Common fields for all entities (id, timestamps)
- **APIResponse<T>**: Generic API response wrapper
- **PaginatedResponse<T>**: Paginated API response
- **ValidationResult<T>**: Validation result with errors

### Authentication

- **User**: Complete user entity with profile and permissions
- **UserRole**: Enum of user roles (admin, author, etc.)
- **LoginRequest**: Login form data
- **JWTPayload**: JWT token structure

### Blog System

- **Post**: Blog post with metadata, SEO, and media
- **Category**: Post categorization
- **Tag**: Post tagging system
- **Comment**: Comment system with moderation

### Validation

- **validateWithSchema()**: JSON schema validation
- **ZodSchemas**: Runtime validation schemas
- **ValidationUtils**: Utility functions for common validations

## Configuration

### TypeScript Configuration

The package includes a strict TypeScript configuration:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### ESLint Configuration

Comprehensive linting rules for type safety:

- TypeScript-specific rules
- Import organization
- Code style consistency
- Error prevention

## Contributing

### Adding New Types

1. **Define the interface** in the appropriate TypeScript file
2. **Add Python equivalent** in the corresponding Python file
3. **Create JSON schema** for validation
4. **Add Zod schema** for runtime validation
5. **Write tests** for the new types
6. **Update documentation**

### Type Naming Conventions

- **Interfaces**: PascalCase (e.g., `UserProfile`)
- **Enums**: PascalCase (e.g., `UserRole`)
- **Properties**: snake_case for API compatibility (e.g., `created_at`)
- **Methods**: camelCase (e.g., `validatePassword`)

### File Organization

```
src/
├── index.ts              # Main exports
├── common.ts             # Common types and utilities
├── auth.ts               # Authentication types
├── user.ts               # User management types
├── blog.ts               # Blog system types
├── api.ts                # API-related types
├── analytics.ts          # Analytics types
├── newsletter.ts         # Newsletter types
├── websocket.ts          # WebSocket types
├── cache.ts              # Caching types
├── database.ts           # Database types
└── validation/           # Validation schemas and utilities
    ├── schemas.ts        # JSON schemas
    └── validators.ts     # Validation functions
```

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:

- **Documentation**: Check the inline TypeScript documentation
- **Issues**: Create an issue in the repository
- **Examples**: See the `__tests__/` directory for usage examples
