# Enterprise Core Package

A comprehensive Python package providing core business logic, utilities, exceptions, validators, and decorators for enterprise Django applications.

## Features

- **Exception Handling**: Comprehensive exception hierarchy with structured error information
- **Utilities**: Common utility functions for slugs, images, text processing, and more
- **Validators**: Security-focused validation functions for content, files, and user input
- **Decorators**: Authentication, authorization, rate limiting, and security decorators
- **Type Safety**: Shared type definitions and validation

## Installation

```bash
pip install -e packages/core/
```

## Quick Start

### Exceptions

```python
from enterprise_core.exceptions import ValidationError, BusinessLogicError

try:
    # Your business logic here
    pass
except Exception as e:
    raise BusinessLogicError("Something went wrong", code="BUSINESS_ERROR")
```

### Utilities

```python
from enterprise_core.utils import generate_unique_slug, calculate_reading_time

# Generate a unique slug
slug = generate_unique_slug(MyModel, "My Blog Post Title")

# Calculate reading time
reading_time = calculate_reading_time(content)
```

### Validators

```python
from enterprise_core.validators import validate_html_content, validate_password_strength

# Validate HTML content for security
validate_html_content("<p>Safe content</p>")

# Validate password strength
validate_password_strength("StrongP@ssw0rd123")
```

### Decorators

```python
from enterprise_core.decorators import require_authentication, rate_limit

@require_authentication()
@rate_limit(requests_per_minute=30)
def my_view(request):
    return JsonResponse({"status": "success"})
```

## Components

### Exception Hierarchy

- `BusinessLogicError`: Base exception for business logic errors
- `ValidationError`: Validation-specific errors
- `AuthenticationError`: Authentication-related errors
- `ContentError`: Content-related errors
- And many more specific exceptions...

### Utility Functions

- `generate_unique_slug()`: Generate unique slugs for models
- `calculate_reading_time()`: Calculate estimated reading time
- `process_uploaded_image()`: Process and optimize uploaded images
- `send_notification_email()`: Send templated notification emails
- `clean_html_content()`: Clean HTML content for security

### Validators

- `validate_slug_format()`: Validate slug format and reserved words
- `validate_html_content()`: Validate HTML for security threats
- `validate_password_strength()`: Validate password complexity
- `validate_email_domain()`: Validate email domains against blacklists
- `validate_image_file()`: Validate uploaded image files

### Decorators

- `@require_authentication()`: Require user authentication
- `@require_permission()`: Require specific permissions
- `@require_role()`: Require group membership
- `@rate_limit()`: Implement rate limiting
- `@validate_content_security()`: Validate content for security threats

## Development

### Running Tests

```bash
cd packages/core/
python -m pytest
```

### Code Formatting

```bash
black src/
isort src/
flake8 src/
```

### Building the Package

```bash
python -m build
```

## Requirements

- Python 3.8+
- Django 4.0+
- Pillow (for image processing)
- bleach (for HTML cleaning)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Changelog

### Version 1.0.0

- Initial release
- Core exception hierarchy
- Utility functions for common operations
- Security-focused validators
- Authentication and authorization decorators
- Rate limiting and access logging
- Image processing utilities
- SEO and content utilities
