# Development Tools and Automation

This directory contains comprehensive development tools and automation scripts for the fullstack monolith transformation project.

## Overview

The tools in this directory provide:

- **Automatic code generation** for Django apps and Next.js components
- **Hot reloading** with intelligent file watching
- **Database automation** with migration, seeding, and backup capabilities
- **Type generation** from Django models to TypeScript
- **API client generation** from Django REST Framework
- **Development environment setup** with one-command installation
- **Code quality validation** and metrics collection

## Quick Start

### Setup Development Environment

```bash
# One-command setup (Unix/Linux/macOS)
./tools/setup-dev-environment.sh

# One-command setup (Windows)
.\tools\setup-dev-environment.ps1

# Or use Make command
make setup-dev-env
```

### Start Development with Hot Reloading

```bash
# Start all services with hot reloading
make dev

# Or use hot reload manager directly
node tools/hot-reload-config.js start
```

## Tools Directory Structure

```
tools/
├── README.md                           # This file
├── setup-dev-environment.sh           # Unix/Linux/macOS setup script
├── setup-dev-environment.ps1          # Windows setup script
├── hot-reload-config.js               # Hot reloading manager
├── hot-reload.config.json             # Hot reload configuration
├── type-generator.py                  # TypeScript type generation
├── api-client-generator.py            # API client generation
├── db-automation.py                   # Database automation
├── code-quality-validator.js          # Code quality validation
├── test-runner.js                     # Test automation
├── setup-code-quality.ps1            # Code quality setup
├── setup-testing.ps1                 # Testing setup
├── setup-testing.sh                  # Testing setup (Unix)
├── cache/                             # Cache tools
│   ├── cache-benchmark.py             # Cache performance benchmarking
│   ├── cache-monitor.py               # Cache monitoring
│   ├── cache-benchmark-config.json    # Benchmark configuration
│   └── cache-monitor-config.json      # Monitor configuration
└── templates/                         # Code generation templates
    ├── django-app.template.py         # Django app generator
    └── nextjs-component.template.js   # Next.js component generator
```

## Tool Documentation

### 1. Development Environment Setup

**Files:** `setup-dev-environment.sh`, `setup-dev-environment.ps1`

Comprehensive setup scripts that:
- Check and validate prerequisites
- Install all dependencies (Node.js, Python, packages)
- Setup environment configuration files
- Initialize database with migrations and sample data
- Configure Docker environment
- Setup code quality tools and pre-commit hooks
- Generate TypeScript types and API client
- Create development scripts and IDE configuration

**Usage:**
```bash
# Basic setup
./tools/setup-dev-environment.sh

# Skip specific components
./tools/setup-dev-environment.sh --skip-database --skip-docker

# Force overwrite existing files
./tools/setup-dev-environment.sh --force

# Setup for specific environment
./tools/setup-dev-environment.sh --environment staging
```

**Features:**
- ✅ Prerequisite validation
- ✅ Dependency installation
- ✅ Environment configuration
- ✅ Database setup and seeding
- ✅ Docker configuration
- ✅ Code quality tools
- ✅ IDE configuration (VS Code)
- ✅ Development scripts creation

### 2. Hot Reloading System

**Files:** `hot-reload-config.js`, `hot-reload.config.json`

Intelligent hot reloading system that watches for file changes and automatically restarts services:

**Watched Services:**
- **Django API:** Python files, package changes
- **Next.js Web:** TypeScript/JavaScript files, component changes
- **Type Generation:** Django model changes
- **API Client Generation:** Django views, serializers, URLs

**Usage:**
```bash
# Start all services
node tools/hot-reload-config.js start

# Start specific service
node tools/hot-reload-config.js start django
node tools/hot-reload-config.js start nextjs

# List available services
node tools/hot-reload-config.js list

# Stop all services
node tools/hot-reload-config.js stop

# Restart services
node tools/hot-reload-config.js restart
```

**Configuration:**
```json
{
  "services": {
    "django": {
      "command": "python manage.py runserver 0.0.0.0:8000",
      "cwd": "apps/api",
      "watchPaths": ["apps/api/**/*.py", "packages/**/*.py"],
      "restartDelay": 1000,
      "enabled": true
    }
  }
}
```

### 3. TypeScript Type Generation

**File:** `type-generator.py`

Automatically generates TypeScript interfaces from Django models with:
- Field type mapping (CharField → string, IntegerField → number, etc.)
- Optional field detection (null, blank, default values)
- Relationship handling (ForeignKey, ManyToMany)
- Choice field union types
- API response type generation

**Usage:**
```bash
# Generate once
python tools/type-generator.py

# Watch for changes
python tools/type-generator.py --watch

# Custom paths
python tools/type-generator.py --django-path apps/api --output-path packages/types/src/generated

# Using Make
make generate-types
make generate-types-watch
```

**Generated Files:**
- `packages/types/src/generated/{app}.types.ts` - App-specific types
- `packages/types/src/generated/api.types.ts` - Common API types
- `packages/types/src/generated/index.ts` - Type exports

### 4. API Client Generation

**File:** `api-client-generator.py`

Generates TypeScript API client from Django REST Framework with:
- Service classes for each model
- CRUD operations (list, create, retrieve, update, delete)
- Custom action support
- Authentication handling with token refresh
- Request/response interceptors
- Error handling and retry mechanisms

**Usage:**
```bash
# Generate once
python tools/api-client-generator.py

# Watch for changes
python tools/api-client-generator.py --watch

# Using Make
make generate-api-client
make generate-api-client-watch
```

**Generated Files:**
- `packages/api-client/src/generated/index.ts` - Main API client
- `packages/api-client/src/generated/config.ts` - Configuration

### 5. Database Automation

**File:** `db-automation.py`

Comprehensive database management with:
- Migration creation and application
- Migration rollback capabilities
- Environment-specific data seeding
- Database backup and restore
- Schema validation and optimization
- Superuser creation

**Usage:**
```bash
# Migrations
python tools/db-automation.py makemigrations
python tools/db-automation.py migrate
python tools/db-automation.py rollback app_name migration_name

# Data management
python tools/db-automation.py seed --env development
python tools/db-automation.py backup --name my_backup
python tools/db-automation.py restore backup.json

# Utilities
python tools/db-automation.py validate
python tools/db-automation.py optimize
python tools/db-automation.py createsuperuser --username admin --email admin@example.com --password admin123

# Using Make
make db-migrate
make db-seed
make db-backup
make db-restore BACKUP_FILE=backup.json
```

**Features:**
- ✅ Migration management with rollback
- ✅ Environment-specific seeding (development, testing, staging, production)
- ✅ Automated backup with timestamps
- ✅ Schema validation and optimization
- ✅ Fixture generation and management

### 6. Code Generation Templates

#### Django App Template

**File:** `templates/django-app.template.py`

Generates complete Django apps with:
- Models with proper relationships and validation
- Serializers with comprehensive field handling
- ViewSets with permissions and filtering
- URL patterns with API versioning
- Admin interface configuration
- Tests with factory-based data generation
- Permissions and filters

**Usage:**
```bash
# Using example configuration
python tools/templates/django-app.template.py blog --example

# Using custom configuration
python tools/templates/django-app.template.py myapp --config myapp-config.json

# Using Make
make generate-django-app APP_NAME=blog CONFIG=blog-config.json
```

**Configuration Example:**
```json
{
  "description": "Blog management functionality",
  "models": {
    "post": {
      "description": "Blog post model",
      "fields": {
        "title": {"type": "char", "max_length": 200},
        "content": {"type": "text"},
        "author": {"type": "foreign_key", "related_model": "User"},
        "status": {
          "type": "char",
          "choices": [["draft", "Draft"], ["published", "Published"]],
          "default": "draft"
        }
      }
    }
  }
}
```

#### Next.js Component Template

**File:** `templates/nextjs-component.template.js`

Generates React components with:
- TypeScript interfaces and prop types
- Tailwind CSS styling
- Storybook stories with controls
- Unit tests with React Testing Library
- Accessibility features
- Multiple component variants

**Usage:**
```bash
# Using preset
node tools/templates/nextjs-component.template.js Button --preset button

# Using custom configuration
node tools/templates/nextjs-component.template.js MyComponent --config component-config.json

# Using Make
make generate-nextjs-component COMPONENT_NAME=Button PRESET=button
```

**Available Presets:**
- `button` - Button component with variants and sizes
- `card` - Card component for content display
- `modal` - Modal dialog with accessibility features

### 7. Code Quality Tools

**Files:** `code-quality-validator.js`, `setup-code-quality.ps1`

Comprehensive code quality validation:
- ESLint and Prettier for JavaScript/TypeScript
- Black, isort, and Flake8 for Python
- Pre-commit hooks configuration
- Security scanning with Bandit and Safety
- Dependency vulnerability checking
- Code complexity analysis

**Usage:**
```bash
# Setup code quality tools
./tools/setup-code-quality.ps1

# Validate code quality
node tools/code-quality-validator.js

# Using Make
make quality-check
make setup-code-quality
make validate-code-quality
```

### 8. Cache Tools

**Files:** `cache/cache-benchmark.py`, `cache/cache-monitor.py`

Cache performance tools:
- Benchmark different caching strategies
- Monitor cache performance in real-time
- Generate performance reports
- Export metrics in Prometheus format

**Usage:**
```bash
# Run benchmarks
python tools/cache/cache-benchmark.py --config tools/cache/cache-benchmark-config.json

# Monitor cache performance
python tools/cache/cache-monitor.py --config tools/cache/cache-monitor-config.json

# Using Make
make cache-benchmark
make cache-monitor
make cache-report
```

## Integration with Make Commands

All tools are integrated with the project's Makefile for easy access:

### Development Commands
```bash
make dev                    # Start hot reload development
make setup-dev-env          # Setup development environment
make generate-types         # Generate TypeScript types
make generate-api-client    # Generate API client
```

### Database Commands
```bash
make db-migrate            # Run migrations
make db-seed               # Seed development data
make db-backup             # Create backup
make db-restore            # Restore backup
make db-validate           # Validate schema
```

### Code Generation Commands
```bash
make generate-django-app APP_NAME=myapp
make generate-nextjs-component COMPONENT_NAME=Button PRESET=button
```

### Quality Commands
```bash
make quality-check         # Comprehensive quality check
make setup-code-quality    # Setup quality tools
make validate-code-quality # Validate configuration
```

## Configuration Files

### Hot Reload Configuration (`hot-reload.config.json`)

Controls which services are watched and how they restart:

```json
{
  "services": {
    "django": {
      "command": "python manage.py runserver 0.0.0.0:8000",
      "cwd": "apps/api",
      "env": {"DJANGO_SETTINGS_MODULE": "config.settings.development"},
      "watchPaths": ["apps/api/**/*.py", "packages/**/*.py"],
      "ignorePaths": ["**/__pycache__/**", "**/*.pyc"],
      "restartDelay": 1000,
      "enabled": true
    }
  },
  "global": {
    "clearConsole": true,
    "showTimestamps": true,
    "colorOutput": true
  }
}
```

### Cache Configuration

**Benchmark Config (`cache/cache-benchmark-config.json`):**
```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0
  },
  "tests": {
    "operations": 10000,
    "key_size": 100,
    "value_size": 1000
  }
}
```

**Monitor Config (`cache/cache-monitor-config.json`):**
```json
{
  "redis": {
    "host": "localhost",
    "port": 6379
  },
  "monitoring": {
    "interval": 5,
    "metrics": ["memory", "operations", "connections"]
  }
}
```

## Best Practices

### 1. Development Workflow

1. **Setup:** Run `make setup-dev-env` once
2. **Development:** Use `make dev` for hot reloading
3. **Code Generation:** Use templates for consistent code structure
4. **Database:** Use automation tools for migrations and seeding
5. **Quality:** Run `make quality-check` before commits

### 2. Code Generation

1. **Django Apps:** Always use templates for consistent structure
2. **Components:** Use presets when possible, customize as needed
3. **Types:** Regenerate after model changes
4. **API Client:** Regenerate after API changes

### 3. Database Management

1. **Migrations:** Use automation tools for consistency
2. **Seeding:** Use environment-specific data
3. **Backups:** Create before major changes
4. **Validation:** Run before deployments

### 4. Hot Reloading

1. **File Watching:** Configure appropriate ignore patterns
2. **Restart Delays:** Adjust based on service startup time
3. **Resource Usage:** Monitor file watcher limits
4. **Service Dependencies:** Start services in correct order

## Troubleshooting

### Common Issues

1. **File Watcher Limits (Linux):**
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

2. **Python Path Issues:**
   ```bash
   export PYTHONPATH="packages/core/src:packages/auth/src:packages/cache/src:packages/database/src:packages/config/src"
   ```

3. **Node.js Memory Issues:**
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   ```

4. **Django Setup Issues:**
   ```bash
   cd apps/api
   python manage.py check
   ```

### Getting Help

1. **Check logs:** Each tool provides detailed logging
2. **Validate setup:** Use `make validate-code-quality`
3. **Reset environment:** Use setup scripts with `--force`
4. **Check documentation:** Each tool has built-in help (`--help`)

## Contributing

When adding new tools:

1. **Follow naming conventions:** Use descriptive names with appropriate extensions
2. **Add documentation:** Include comprehensive docstrings and comments
3. **Integrate with Make:** Add appropriate Makefile targets
4. **Add tests:** Include unit tests for complex logic
5. **Update README:** Document new tools and usage

## Future Enhancements

Planned improvements:
- [ ] GUI interface for tool management
- [ ] Integration with CI/CD pipelines
- [ ] Performance monitoring dashboard
- [ ] Automated dependency updates
- [ ] Code generation from OpenAPI specs
- [ ] Database schema migration validation
- [ ] Real-time collaboration features

---

This tools directory provides a comprehensive development automation suite that significantly improves developer productivity and code quality consistency across the fullstack monolith transformation project.