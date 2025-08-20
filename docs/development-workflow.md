# Development Workflow Guide

This guide covers the complete development workflow for the fullstack monolith transformation project, including setup, development practices, testing, and deployment procedures.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment Setup](#development-environment-setup)
- [Development Tools and Automation](#development-tools-and-automation)
- [Code Generation](#code-generation)
- [Hot Reloading and Live Development](#hot-reloading-and-live-development)
- [Database Management](#database-management)
- [Testing Workflow](#testing-workflow)
- [Code Quality and Standards](#code-quality-and-standards)
- [Git Workflow](#git-workflow)
- [Deployment Workflow](#deployment-workflow)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

Ensure you have the following installed:

- **Node.js** (v18+) and npm
- **Python** (3.9+) and pip
- **Git**
- **Docker** and Docker Compose (optional but recommended)
- **PostgreSQL** (or use Docker)

### One-Command Setup

```bash
# For Unix/Linux/macOS
./tools/setup-dev-environment.sh

# For Windows
.\tools\setup-dev-environment.ps1
```

### Manual Setup

```bash
# 1. Install dependencies
make install

# 2. Setup environment
cp .env.example .env
cp apps/api/.env.development.example apps/api/.env
cp apps/web/.env.development.example apps/web/.env.local

# 3. Setup database
make db-migrate
make db-seed

# 4. Start development servers
make dev
```

## Development Environment Setup

### Environment Configuration

The project uses environment-specific configuration files:

```
.env                           # Root environment variables
apps/api/.env                  # Django API configuration
apps/web/.env.local           # Next.js web app configuration
```

#### Key Environment Variables

**Root (.env):**
```bash
NODE_ENV=development
COMPOSE_PROJECT_NAME=fullstack-blog
```

**Django API (apps/api/.env):**
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**Next.js Web (apps/web/.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXTAUTH_SECRET=your-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
```

### IDE Configuration

The setup script creates VS Code configuration with:

- Python interpreter path
- Linting and formatting settings
- TypeScript configuration
- Recommended extensions

**Recommended VS Code Extensions:**
- Python
- Flake8
- Black Formatter
- Tailwind CSS IntelliSense
- Prettier
- TypeScript and JavaScript Language Features

## Development Tools and Automation

### Available Make Commands

```bash
# Development
make dev                    # Start all development servers
make dev-api               # Start Django API only
make dev-web               # Start Next.js web only
make dev-docker            # Start with Docker

# Building
make build                 # Build all applications
make build-web             # Build Next.js application
make build-api             # Build Django API (collect static)

# Testing
make test                  # Run all tests
make test-web              # Run Next.js tests
make test-api              # Run Django API tests
make test-e2e              # Run end-to-end tests
make test-coverage         # Run tests with coverage

# Code Quality
make lint                  # Run linting for all code
make format                # Format all code
make type-check            # Run type checking
make quality-check         # Comprehensive quality checks

# Database
make db-migrate            # Run Django migrations
make db-seed               # Seed database with sample data
make db-reset              # Reset database (WARNING: destroys data)

# Docker
make docker-up             # Start Docker containers
make docker-down           # Stop Docker containers
make docker-build          # Build Docker images

# Utilities
make generate-types        # Generate TypeScript types
make generate-api-client   # Generate API client
make clean                 # Clean build artifacts
```

### Hot Reloading Configuration

The project includes a sophisticated hot reloading system that watches for changes and automatically restarts services:

```bash
# Start hot reload manager
node tools/hot-reload-config.js start

# Start specific service
node tools/hot-reload-config.js start django
node tools/hot-reload-config.js start nextjs

# List available services
node tools/hot-reload-config.js list
```

**Watched Files:**
- **Django API:** `apps/api/**/*.py`, `packages/**/*.py`
- **Next.js Web:** `apps/web/**/*.{js,jsx,ts,tsx}`, `packages/api-client/**/*.ts`
- **Type Generation:** `apps/api/**/models.py`
- **API Client Generation:** `apps/api/**/views.py`, `apps/api/**/serializers.py`

## Code Generation

### Django App Generation

Generate complete Django apps with models, serializers, views, and tests:

```bash
# Using example configuration
python tools/templates/django-app.template.py blog --example

# Using custom configuration
python tools/templates/django-app.template.py myapp --config myapp-config.json
```

**Example Configuration (myapp-config.json):**
```json
{
  "description": "My custom app functionality",
  "models": {
    "item": {
      "description": "Item model",
      "str_field": "name",
      "fields": {
        "name": {"type": "char", "max_length": 100},
        "description": {"type": "text", "blank": true},
        "price": {"type": "decimal", "max_digits": 10, "decimal_places": 2},
        "is_active": {"type": "boolean", "default": true}
      }
    }
  }
}
```

### Next.js Component Generation

Generate React components with TypeScript, tests, and Storybook stories:

```bash
# Using preset
node tools/templates/nextjs-component.template.js Button --preset button

# Using custom configuration
node tools/templates/nextjs-component.template.js MyComponent --config component-config.json
```

**Available Presets:**
- `button` - Button component with variants
- `card` - Card component for content display
- `modal` - Modal dialog component

### TypeScript Type Generation

Automatically generate TypeScript types from Django models:

```bash
# Generate once
python tools/type-generator.py

# Watch for changes
python tools/type-generator.py --watch

# Custom paths
python tools/type-generator.py --django-path apps/api --output-path packages/types/src/generated
```

### API Client Generation

Generate TypeScript API client from Django REST Framework:

```bash
# Generate once
python tools/api-client-generator.py

# Watch for changes
python tools/api-client-generator.py --watch

# Custom paths
python tools/api-client-generator.py --django-path apps/api --output-path packages/api-client/src/generated
```

## Hot Reloading and Live Development

### Configuration

Hot reloading is configured in `tools/hot-reload.config.json`:

```json
{
  "services": {
    "django": {
      "command": "python manage.py runserver 0.0.0.0:8000",
      "cwd": "apps/api",
      "watchPaths": ["apps/api/**/*.py", "packages/**/*.py"],
      "restartDelay": 1000,
      "enabled": true
    },
    "nextjs": {
      "command": "npm run dev",
      "cwd": "apps/web",
      "watchPaths": ["apps/web/**/*.{js,jsx,ts,tsx}"],
      "restartDelay": 500,
      "enabled": true
    }
  }
}
```

### Usage

```bash
# Start all services with hot reloading
make dev

# Or use the hot reload manager directly
node tools/hot-reload-config.js start

# Start specific services
node tools/hot-reload-config.js start django
node tools/hot-reload-config.js start nextjs

# Restart all services
node tools/hot-reload-config.js restart

# Stop all services
node tools/hot-reload-config.js stop
```

## Database Management

### Migration Workflow

```bash
# Create migrations
python tools/db-automation.py makemigrations

# Apply migrations
python tools/db-automation.py migrate

# Show migration status
python tools/db-automation.py status

# Rollback migration
python tools/db-automation.py rollback app_name migration_name
```

### Data Seeding

```bash
# Seed development data
python tools/db-automation.py seed --env development

# Seed testing data
python tools/db-automation.py seed --env testing

# Seed staging data
python tools/db-automation.py seed --env staging
```

### Backup and Restore

```bash
# Create backup
python tools/db-automation.py backup --name my_backup

# Restore backup
python tools/db-automation.py restore my_backup.json --flush

# List backups
ls backups/database/
```

### Database Utilities

```bash
# Validate schema
python tools/db-automation.py validate

# Optimize database
python tools/db-automation.py optimize

# Reset database (WARNING: destroys data)
python tools/db-automation.py reset --confirm

# Create superuser
python tools/db-automation.py createsuperuser --username admin --email admin@example.com --password admin123
```

## Testing Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific test suites
make test-web              # Next.js tests
make test-api              # Django API tests
make test-packages         # Shared package tests
make test-e2e              # End-to-end tests

# Run with coverage
make test-coverage

# Run specific test files
cd apps/api && python -m pytest apps/blog/tests/test_models.py
cd apps/web && npm test -- Button.test.tsx
```

### Test Configuration

**Django API Tests:**
- Uses pytest with factory_boy for test data
- Database isolation with pytest-django
- Coverage reporting with pytest-cov

**Next.js Tests:**
- Jest with React Testing Library
- Component testing with user interactions
- Snapshot testing for UI consistency

**End-to-End Tests:**
- Playwright for cross-browser testing
- Page object model for maintainability
- Visual regression testing

### Writing Tests

**Django Model Test Example:**
```python
from django.test import TestCase
from .factories import PostFactory

class PostModelTest(TestCase):
    def setUp(self):
        self.post = PostFactory()
    
    def test_str_representation(self):
        self.assertEqual(str(self.post), self.post.title)
```

**React Component Test Example:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });
  
  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## Code Quality and Standards

### Linting and Formatting

```bash
# Run all linting
make lint

# Run specific linting
make lint-web              # ESLint for Next.js
make lint-api              # Flake8 for Django
make lint-packages         # Flake8 for packages

# Format all code
make format

# Format specific code
make format-web            # Prettier for Next.js
make format-api            # Black for Django
make format-packages       # Black for packages
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
make pre-commit-install

# Run hooks manually
make pre-commit-run

# Update hooks
make pre-commit-update
```

**Configured Hooks:**
- Black (Python formatting)
- isort (Python import sorting)
- Flake8 (Python linting)
- Prettier (JavaScript/TypeScript formatting)
- ESLint (JavaScript/TypeScript linting)
- Trailing whitespace removal
- End-of-file fixing

### Code Quality Validation

```bash
# Comprehensive quality check
make quality-check

# Individual checks
make type-check            # TypeScript and Python type checking
make security-lint         # Security-focused linting
make complexity-check      # Code complexity analysis
make dead-code-check       # Unused code detection
make dependency-check      # Dependency vulnerability scan
```

### Quality Metrics

```bash
# Generate code metrics
make code-metrics

# SonarQube analysis (if configured)
make sonar-scan

# View reports
ls reports/
```

## Git Workflow

### Branch Strategy

We use a modified Git Flow strategy:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development branches
- `release/*` - Release preparation branches
- `hotfix/*` - Critical bug fixes

### Commit Convention

We follow Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Build/tooling changes

**Examples:**
```
feat(auth): add multi-factor authentication
fix(api): resolve user registration validation
docs(readme): update installation instructions
```

### Development Workflow

1. **Create Feature Branch:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-new-feature
   ```

2. **Development:**
   ```bash
   # Make changes
   git add .
   git commit -m "feat(scope): add new functionality"
   ```

3. **Testing:**
   ```bash
   make test
   make quality-check
   ```

4. **Push and Create PR:**
   ```bash
   git push origin feature/my-new-feature
   # Create pull request via GitHub/GitLab
   ```

5. **Code Review and Merge:**
   - Address review feedback
   - Ensure CI passes
   - Merge to develop

## Deployment Workflow

### Development Deployment

```bash
# Start development environment
make dev

# Or with Docker
make docker-up
```

### Staging Deployment

```bash
# Build for staging
make build

# Deploy to staging (example with Docker)
docker-compose -f docker-compose.staging.yml up -d

# Run migrations
make docker-migrate

# Verify deployment
make health-check
```

### Production Deployment

```bash
# Build production images
make build-docker-prod

# Deploy to production
make prod-deploy

# Monitor deployment
make prod-status

# Rollback if needed
make prod-rollback
```

### CI/CD Pipeline

The project includes GitHub Actions workflows:

- **Test Pipeline:** Runs on every PR
- **Build Pipeline:** Builds Docker images
- **Deploy Pipeline:** Deploys to staging/production
- **Security Pipeline:** Runs security scans

## Troubleshooting

### Common Issues

#### Development Server Won't Start

1. **Check dependencies:**
   ```bash
   make install
   ```

2. **Check environment variables:**
   ```bash
   # Ensure .env files exist and are configured
   ls -la .env*
   ```

3. **Check database connection:**
   ```bash
   # Test PostgreSQL connection
   psql -U postgres -c "SELECT 1;"
   ```

#### Hot Reloading Not Working

1. **Check file watchers:**
   ```bash
   # Increase file watcher limit (Linux)
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

2. **Check hot reload configuration:**
   ```bash
   node tools/hot-reload-config.js list
   ```

#### Type Generation Fails

1. **Check Django setup:**
   ```bash
   cd apps/api
   python manage.py check
   ```

2. **Check Python path:**
   ```bash
   export PYTHONPATH="packages/core/src:packages/auth/src:packages/cache/src:packages/database/src:packages/config/src"
   ```

#### Tests Failing

1. **Check test database:**
   ```bash
   cd apps/api
   python manage.py test --debug-mode
   ```

2. **Clear test cache:**
   ```bash
   cd apps/web
   npm test -- --clearCache
   ```

### Getting Help

1. **Check logs:**
   ```bash
   # Application logs
   tail -f apps/api/logs/django.log
   tail -f apps/web/logs/nextjs.log
   
   # Docker logs
   docker-compose logs -f
   ```

2. **Run diagnostics:**
   ```bash
   make health-check
   make validate-code-quality
   ```

3. **Reset environment:**
   ```bash
   # Clean and reinstall
   make clean
   make install
   
   # Reset database
   make db-reset
   make db-seed
   ```

### Performance Optimization

#### Development Performance

1. **Use Docker for services:**
   ```bash
   # Start only database and Redis with Docker
   docker-compose up -d postgres redis
   
   # Run apps natively
   make dev-api
   make dev-web
   ```

2. **Optimize file watching:**
   ```bash
   # Exclude large directories from watching
   # Edit tools/hot-reload.config.json
   ```

3. **Use incremental builds:**
   ```bash
   # Next.js incremental builds
   cd apps/web
   npm run dev -- --turbo
   ```

#### Production Performance

1. **Enable caching:**
   ```bash
   # Redis cluster for distributed caching
   make cache-setup
   ```

2. **Optimize database:**
   ```bash
   make db-optimize
   ```

3. **Monitor performance:**
   ```bash
   make monitor-metrics
   ```

---

This development workflow guide provides comprehensive coverage of all development tools and automation created in Task 25. The tools include hot reloading, code generation, database automation, and complete development environment setup scripts.