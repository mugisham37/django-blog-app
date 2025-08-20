# Enterprise Blog Testing Suite

Comprehensive testing infrastructure for the enterprise blog platform monorepo.

## Overview

This testing suite provides complete coverage for all components of the enterprise blog platform:

- **Unit Tests**: Individual component and function testing
- **Integration Tests**: Cross-component interaction testing  
- **End-to-End Tests**: Full user workflow testing
- **API Tests**: REST API endpoint testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization testing

## Quick Start

```bash
# Install dependencies
npm run setup

# Run all tests
npm test

# Run specific test suite
npm run test:unit
npm run test:e2e
npm run test:api
npm run test:performance

# Run with coverage
npm run test:coverage

# Watch mode for development
npm run test:watch
```

## Test Structure

```
tests/
├── django/                 # Django API tests
│   ├── conftest.py         # Django test configuration
│   ├── test_authentication.py
│   └── test_api_endpoints.py
├── frontend/               # Next.js frontend tests
│   ├── components/         # Component tests
│   ├── pages/             # Page tests
│   └── setup.js           # Frontend test setup
├── packages/              # Package-specific tests
│   ├── api-client/        # API client tests
│   ├── auth/              # Auth package tests
│   └── cache/             # Cache package tests
├── e2e/                   # End-to-end tests
│   ├── auth.spec.ts       # Authentication flows
│   ├── blog.spec.ts       # Blog functionality
│   └── global-setup.ts    # E2E test setup
├── api/                   # API testing
│   ├── postman-collection.json
│   └── environments/      # Test environments
├── performance/           # Performance tests
│   ├── load-test.js       # Load testing
│   └── stress-test.js     # Stress testing
├── mocks/                 # Mock data and handlers
│   ├── handlers.js        # MSW request handlers
│   └── server.js          # Mock server setup
└── coverage/              # Coverage reports
```

## Test Types

### Unit Tests

Test individual components, functions, and modules in isolation.

```bash
# Run all unit tests
npm run test:unit

# Run Django unit tests
npm run test:django:unit

# Run frontend unit tests
npm run test:unit -- --testPathPattern=frontend
```

**Coverage Requirements:**
- Core packages: 90%
- Auth package: 90%
- Other packages: 85%
- Frontend components: 85%

### Integration Tests

Test interactions between different components and systems.

```bash
# Run integration tests
npm run test:integration

# Django integration tests
npm run test:django:integration
```

### End-to-End Tests

Test complete user workflows across the entire application.

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode
npx playwright test --headed

# Run specific E2E test
npx playwright test auth.spec.ts
```

**E2E Test Coverage:**
- User authentication flows
- Blog post creation and management
- Comment system
- Search functionality
- Admin operations

### API Tests

Test REST API endpoints using Postman collections.

```bash
# Run API tests
npm run test:api

# Run with specific environment
newman run api/postman-collection.json -e api/environments/staging.json
```

**API Test Coverage:**
- Authentication endpoints
- CRUD operations
- Search and filtering
- Error handling
- Rate limiting

### Performance Tests

Test system performance under various load conditions.

```bash
# Run load tests
npm run test:performance

# Run stress tests
npm run test:stress

# Run with custom configuration
k6 run performance/load-test.js --vus 50 --duration 5m
```

**Performance Benchmarks:**
- Response time: 95% < 2s
- Error rate: < 10%
- Concurrent users: 200+
- Throughput: 1000+ req/min

## Configuration

### Environment Variables

```bash
# Test environment
NODE_ENV=test

# API endpoints
API_BASE_URL=http://localhost:8000/api/v1
WEB_BASE_URL=http://localhost:3000

# Database
TEST_DATABASE_URL=sqlite:///test.db

# Performance testing
K6_VUS=10
K6_DURATION=5m
```

### Coverage Thresholds

Coverage thresholds are configured in `coverage/coverage.config.js`:

```javascript
coverageThreshold: {
  global: {
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80,
  },
  'packages/auth/': {
    branches: 90,
    functions: 90,
    lines: 90,
    statements: 90,
  },
}
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Tests
  run: |
    npm run setup
    npm run test:ci
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./tests/coverage/lcov.info
```

### Quality Gates

Tests must pass these quality gates:

1. **Unit Test Coverage**: ≥ 80% overall, ≥ 90% for critical packages
2. **Integration Tests**: All must pass
3. **E2E Tests**: All critical user flows must pass
4. **API Tests**: All endpoints must respond correctly
5. **Performance Tests**: Must meet response time and throughput benchmarks
6. **Security Tests**: No security vulnerabilities detected

## Writing Tests

### Unit Test Example

```javascript
// tests/frontend/components/LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { LoginForm } from '../../../apps/web/src/components/LoginForm'

describe('LoginForm', () => {
  it('submits form with valid credentials', async () => {
    render(<LoginForm />)
    
    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'testuser' }
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    expect(mockLogin).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123'
    })
  })
})
```

### E2E Test Example

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test('user can login and access dashboard', async ({ page }) => {
  await page.goto('/auth/login')
  
  await page.fill('[data-testid="username"]', 'testuser')
  await page.fill('[data-testid="password"]', 'password123')
  await page.click('[data-testid="login-button"]')
  
  await expect(page).toHaveURL('/dashboard')
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
})
```

### Django Test Example

```python
# tests/django/test_authentication.py
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.auth
def test_user_login(api_client, user):
    url = reverse('auth:login')
    data = {
        'username': user.username,
        'password': 'testpassword'
    }
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.data
```

## Debugging Tests

### Frontend Tests

```bash
# Run tests in debug mode
npm run test:unit -- --detectOpenHandles --forceExit

# Run specific test file
npm run test:unit LoginForm.test.tsx

# Update snapshots
npm run test:unit -- --updateSnapshot
```

### E2E Tests

```bash
# Run in headed mode
npx playwright test --headed

# Debug specific test
npx playwright test --debug auth.spec.ts

# Generate test code
npx playwright codegen localhost:3000
```

### Django Tests

```bash
# Run with verbose output
python -m pytest tests/django/ -v -s

# Run specific test
python -m pytest tests/django/test_authentication.py::test_user_login

# Run with debugger
python -m pytest tests/django/ --pdb
```

## Troubleshooting

### Common Issues

1. **Tests timing out**
   - Increase timeout in configuration
   - Check for async operations not being awaited
   - Verify test environment is properly set up

2. **Coverage not meeting thresholds**
   - Add tests for uncovered code paths
   - Remove dead code
   - Update coverage configuration if needed

3. **E2E tests failing**
   - Ensure both frontend and backend servers are running
   - Check test data setup in global-setup.ts
   - Verify selectors are correct

4. **Performance tests failing**
   - Check system resources
   - Verify k6 is installed correctly
   - Adjust performance thresholds if needed

### Getting Help

- Check test logs in `tests/reports/`
- Review coverage reports in `tests/coverage/html/`
- Check CI/CD pipeline logs
- Consult team documentation

## Contributing

1. Write tests for all new features
2. Maintain coverage thresholds
3. Follow testing best practices
4. Update documentation as needed
5. Run full test suite before submitting PRs

```bash
# Validate before committing
npm run validate
```