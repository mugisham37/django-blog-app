# Enterprise Database Package

A comprehensive database abstraction layer providing enterprise-grade features including connection pooling, repository patterns, read replica management, and database utilities.

## Features

- **Connection Pooling**: Advanced PostgreSQL connection pooling with pgbouncer-style configuration
- **Read Replica Management**: Automatic read/write splitting for database scaling
- **Repository Pattern**: Base repository classes for clean data access patterns
- **Migration Utilities**: Advanced migration management with rollback capabilities
- **Data Seeding**: Comprehensive data seeding scripts for development and testing
- **Health Monitoring**: Database health checks and performance monitoring
- **Backup Management**: Automated backup and restore procedures
- **Query Optimization**: Query caching and performance optimization tools

## Installation

```bash
pip install -e packages/database/
```

For development:

```bash
pip install -e "packages/database/[dev]"
```

For monitoring features:

```bash
pip install -e "packages/database/[monitoring]"
```

## Quick Start

### Basic Configuration

```python
# settings.py
from enterprise_database.config import get_database_config

DATABASES = {
    'default': get_database_config('production'),
}

# Enable read replica if configured
from enterprise_database.config import setup_read_replica
setup_read_replica(DATABASES)

# Add database router for read/write splitting
DATABASE_ROUTERS = ['enterprise_database.routers.DatabaseRouter']
```

### Repository Pattern Usage

```python
from enterprise_database.repositories import BaseRepository
from myapp.models import User

class UserRepository(BaseRepository):
    model = User

    def get_active_users(self):
        return self.filter(is_active=True)

    def get_by_email(self, email):
        return self.get(email=email)

# Usage
user_repo = UserRepository()
active_users = user_repo.get_active_users()
user = user_repo.get_by_email('user@example.com')
```

### Connection Management

```python
from enterprise_database.connections import ConnectionManager

# Get connection with automatic pooling
with ConnectionManager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()

# Read replica usage
with ConnectionManager.get_read_connection() as conn:
    # This will use read replica if configured
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    results = cursor.fetchall()
```

### Migration Management

```python
from enterprise_database.migrations import MigrationManager

# Run migrations
migration_manager = MigrationManager()
migration_manager.migrate()

# Rollback to specific migration
migration_manager.rollback('0001_initial')

# Check migration status
status = migration_manager.get_status()
```

### Data Seeding

```python
from enterprise_database.seeders import DataSeeder

# Seed development data
seeder = DataSeeder(environment='development')
seeder.seed_all()

# Seed specific data
seeder.seed_users()
seeder.seed_blog_posts()
```

## Configuration

### Environment Variables

```bash
# Database Configuration
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Connection Pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_MAX_CONNS=50
DB_MIN_CONNS=5

# Read Replica (optional)
DB_READ_HOST=read-replica-host
DB_READ_USER=read_user
DB_READ_PASSWORD=read_password

# Performance Tuning
DB_CONN_MAX_AGE=600
DB_STATEMENT_TIMEOUT=30000
DB_LOCK_TIMEOUT=10000

# SSL Configuration
DB_SSL_MODE=require
DB_SSL_CERT=/path/to/cert.pem
DB_SSL_KEY=/path/to/key.pem

# Monitoring
DB_ENABLE_QUERY_LOGGING=true
DB_SLOW_QUERY_THRESHOLD=1.0
DB_METRICS_COLLECTION=true

# Backup
DB_BACKUP_ENABLED=true
DB_BACKUP_SCHEDULE="0 2 * * *"
DB_BACKUP_RETENTION_DAYS=30
```

### Advanced Configuration

```python
# settings.py
from enterprise_database.config import DatabaseConfig

DATABASE_CONFIG = DatabaseConfig(
    pool_size=20,
    max_overflow=40,
    enable_read_replica=True,
    enable_query_cache=True,
    enable_monitoring=True,
    backup_enabled=True,
)

DATABASES = DATABASE_CONFIG.get_databases()
```

## CLI Commands

### Migration Commands

```bash
# Run migrations
db-migrate

# Rollback migrations
db-migrate --rollback 0001_initial

# Check migration status
db-migrate --status

# Create new migration
db-migrate --create migration_name
```

### Seeding Commands

```bash
# Seed all data
db-seed

# Seed specific data
db-seed --users --posts

# Seed for specific environment
db-seed --environment production
```

### Backup Commands

```bash
# Create backup
db-backup

# Restore from backup
db-backup --restore backup_file.sql

# List backups
db-backup --list
```

## Repository Pattern

The package provides a comprehensive repository pattern implementation:

### Base Repository

```python
from enterprise_database.repositories import BaseRepository

class BaseRepository:
    def get(self, **kwargs)
    def filter(self, **kwargs)
    def all(self)
    def create(self, **kwargs)
    def update(self, instance, **kwargs)
    def delete(self, instance)
    def bulk_create(self, objects)
    def bulk_update(self, objects, fields)
    def exists(self, **kwargs)
    def count(self, **kwargs)
```

### Custom Repository Example

```python
from enterprise_database.repositories import BaseRepository
from blog.models import Post

class PostRepository(BaseRepository):
    model = Post

    def get_published_posts(self):
        return self.filter(status='published', published_at__lte=timezone.now())

    def get_posts_by_category(self, category):
        return self.filter(category=category)

    def get_popular_posts(self, limit=10):
        return self.filter(status='published').order_by('-view_count')[:limit]

    def search_posts(self, query):
        return self.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
```

## Connection Pooling

Advanced connection pooling with automatic failover:

```python
from enterprise_database.pools import ConnectionPool

# Configure connection pool
pool = ConnectionPool(
    min_connections=5,
    max_connections=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

# Use pooled connections
with pool.get_connection() as conn:
    # Your database operations
    pass
```

## Read Replica Management

Automatic read/write splitting:

```python
# In your models or repositories
from enterprise_database.decorators import use_read_replica

class PostRepository(BaseRepository):
    model = Post

    @use_read_replica
    def get_published_posts(self):
        # This will use read replica
        return self.filter(status='published')

    def create_post(self, **kwargs):
        # This will use primary database
        return self.create(**kwargs)
```

## Monitoring and Health Checks

Built-in monitoring and health check capabilities:

```python
from enterprise_database.monitoring import DatabaseMonitor

monitor = DatabaseMonitor()

# Check database health
health_status = monitor.check_health()

# Get performance metrics
metrics = monitor.get_metrics()

# Check slow queries
slow_queries = monitor.get_slow_queries()
```

## Testing

Run the test suite:

```bash
cd packages/database
pytest
```

Run with coverage:

```bash
pytest --cov=enterprise_database --cov-report=html
```

## Development

### Setup Development Environment

```bash
cd packages/database
pip install -e ".[dev]"
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

### Running Tests

```bash
pytest tests/
```

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

### 0.1.0 (2024-01-01)

- Initial release
- Basic repository pattern implementation
- Connection pooling support
- Read replica management
- Migration utilities
- Data seeding capabilities
- Health monitoring
- Backup management
