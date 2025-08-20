# Infrastructure Documentation

This directory contains all infrastructure-related configurations for the Fullstack Monolith project, including Docker, Kubernetes, monitoring, and deployment configurations.

## 🐳 Docker Configuration

### Overview

The Docker setup provides a complete containerized environment for development and production deployment. It includes:

- **Django API**: Python/Django backend with Gunicorn
- **Next.js Web**: React/Next.js frontend application
- **PostgreSQL**: Primary database with optimized configuration
- **Redis**: Caching and session storage
- **Nginx**: Reverse proxy and load balancer
- **Celery**: Background task processing
- **Monitoring**: Prometheus and Grafana (production)

### Quick Start

#### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 4GB RAM available for containers
- Ports 80, 3000, 5432, 6379, 8000 available

#### Development Setup

1. **Automated Setup (Recommended)**:

   ```powershell
   # Windows PowerShell
   .\scripts\docker-setup.ps1

   # Linux/Mac Bash
   ./scripts/docker-setup.sh
   ```

2. **Manual Setup**:

   ```bash
   # Copy environment file
   cp .env.docker.example .env.docker

   # Edit environment variables
   # Update .env.docker with your configuration

   # Build and start services
   docker-compose up --build -d

   # Run database migrations
   docker-compose exec django-api python manage.py migrate

   # Create superuser
   docker-compose exec django-api python manage.py createsuperuser
   ```

#### Production Setup

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up --build -d

# Or use the setup script
./scripts/docker-setup.sh --prod
```

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │   Django API    │
│   (Port 3000)   │    │   (Port 8000)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │  Nginx Proxy    │
            │   (Port 80)     │
            └─────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌───────▼───────┐    ┌───▼───┐
│ Redis │    │  PostgreSQL   │    │Celery │
│ Cache │    │   Database    │    │Workers│
└───────┘    └───────────────┘    └───────┘
```

### Environment Configuration

#### Development (.env.docker)

```bash
# Database
POSTGRES_DB=fullstack_blog
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev_password
DATABASE_URL=postgresql://postgres:dev_password@postgres:5432/fullstack_blog

# Redis
REDIS_URL=redis://:redis_password@redis:6379/0
CELERY_BROKER_URL=redis://:redis_password@redis:6379/1

# Django
SECRET_KEY=dev-secret-key
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1,django-api

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=dev-nextauth-secret
```

#### Production (.env.docker)

```bash
# Use strong passwords and secure keys
SECRET_KEY=your-super-secure-secret-key
DEBUG=0
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# SSL Configuration
SSL_CERT_PATH=/etc/nginx/ssl/fullchain.pem
SSL_KEY_PATH=/etc/nginx/ssl/privkey.pem

# Monitoring
SENTRY_DSN=your-sentry-dsn
GRAFANA_PASSWORD=secure-grafana-password
```

### Docker Compose Files

#### docker-compose.yml (Development)

- **Hot reloading** for both Django and Next.js
- **Volume mounts** for live code changes
- **Development tools** (Adminer, Redis Commander, Mailhog)
- **Debug configurations** enabled

#### docker-compose.prod.yml (Production)

- **Optimized images** with multi-stage builds
- **SSL termination** with Nginx
- **Health checks** and restart policies
- **Monitoring stack** (Prometheus, Grafana)
- **Log management** with rotation
- **Security hardening**

#### docker-compose.override.yml

Automatically loaded in development to override base configuration with development-specific settings.

### Container Details

#### Django API Container

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as base
# ... dependencies installation

FROM base as production
# ... application code and static files
CMD ["gunicorn", "config.wsgi:application"]
```

**Features**:

- Non-root user execution
- Health checks
- Static file serving
- Gunicorn with gevent workers
- Comprehensive logging

#### Next.js Web Container

```dockerfile
# Optimized for Next.js standalone output
FROM node:18-alpine AS base
# ... build process
CMD ["node", "server.js"]
```

**Features**:

- Standalone output for minimal image size
- Static file optimization
- Health check endpoint
- Environment variable injection

#### Nginx Reverse Proxy

**Development Configuration**:

- Simple HTTP proxy
- Static file serving
- WebSocket support
- Basic rate limiting

**Production Configuration**:

- SSL/TLS termination
- Advanced security headers
- Comprehensive rate limiting
- Gzip/Brotli compression
- Cache optimization

### Networking

All services communicate through a custom Docker network (`fullstack_network`) with the following internal hostnames:

- `django-api`: Django API server
- `nextjs-web`: Next.js application
- `postgres`: PostgreSQL database
- `redis`: Redis cache
- `nginx`: Reverse proxy

### Volume Management

#### Persistent Volumes

- `postgres_data`: Database files
- `redis_data`: Redis persistence
- `django_static`: Static files
- `django_media`: User uploads
- `django_logs`: Application logs (production)

#### Development Volumes

- Source code mounted for hot reloading
- Node modules cached for faster rebuilds

### Health Checks

All services include comprehensive health checks:

#### Django API (`/health/`)

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": {
    "database": { "status": "healthy" },
    "cache": { "status": "healthy" },
    "redis": { "status": "healthy" }
  }
}
```

#### Next.js (`/api/health`)

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "service": "nextjs-web",
  "checks": {
    "server": { "status": "healthy" },
    "environment": { "status": "healthy" },
    "dependencies": { "status": "healthy" }
  }
}
```

### Monitoring and Logging

#### Development

- **Container logs**: `docker-compose logs -f`
- **Individual service**: `docker-compose logs -f django-api`
- **Real-time monitoring**: Docker Desktop dashboard

#### Production

- **Prometheus**: Metrics collection at `:9090`
- **Grafana**: Dashboards at `:3001`
- **Structured logging**: JSON format with correlation IDs
- **Log rotation**: Automatic cleanup of old logs

### Security Considerations

#### Development

- Default passwords (change for production)
- Debug mode enabled
- Permissive CORS settings
- Development tools exposed

#### Production

- Strong passwords and secrets
- SSL/TLS encryption
- Security headers
- Rate limiting
- Container security scanning
- Non-root user execution
- Read-only file systems where possible

### Backup and Recovery

#### Database Backup

```bash
# Create backup
make docker-backup-db

# Restore backup
make docker-restore-db BACKUP_FILE=backup_20240101_120000.sql
```

#### Volume Backup

```bash
# Backup all volumes
docker run --rm -v fullstack_postgres_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Troubleshooting

#### Common Issues

1. **Port conflicts**:

   ```bash
   # Check port usage
   netstat -tulpn | grep :8000

   # Stop conflicting services
   sudo systemctl stop apache2
   ```

2. **Permission issues**:

   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Database connection issues**:

   ```bash
   # Check database logs
   docker-compose logs postgres

   # Test connection
   docker-compose exec postgres psql -U postgres -d fullstack_blog
   ```

4. **Memory issues**:

   ```bash
   # Check container resource usage
   docker stats

   # Increase Docker memory limit in Docker Desktop
   ```

#### Debug Commands

```bash
# Enter container shell
docker-compose exec django-api bash
docker-compose exec nextjs-web sh

# Check container health
docker-compose ps
docker inspect <container_name>

# View real-time logs
docker-compose logs -f --tail=100

# Restart specific service
docker-compose restart django-api
```

### Performance Optimization

#### Development

- Use `.dockerignore` to exclude unnecessary files
- Enable BuildKit for faster builds
- Use multi-stage builds
- Cache dependencies in separate layers

#### Production

- Use Alpine Linux base images
- Minimize layer count
- Use specific version tags
- Enable image compression
- Implement proper caching strategies

### Scaling

#### Horizontal Scaling

```yaml
# Scale specific services
docker-compose up -d --scale django-api=3 --scale celery-worker=2
```

#### Load Balancing

Nginx automatically load balances between multiple Django API instances.

### Migration to Kubernetes

The Docker configuration is designed to be easily portable to Kubernetes:

- Health checks translate to readiness/liveness probes
- Environment variables map to ConfigMaps/Secrets
- Volumes map to PersistentVolumes
- Services map to Kubernetes Services

See the `infrastructure/k8s/` directory for Kubernetes manifests.

## 📊 Monitoring Stack

### Prometheus Configuration

Located in `monitoring/prometheus/prometheus.yml`:

- Scrapes metrics from Django API
- Monitors container health
- Collects system metrics
- Configurable alerting rules

### Grafana Dashboards

Pre-configured dashboards for:

- Application performance metrics
- Database performance
- Container resource usage
- Business metrics

### Alerting

Configured alerts for:

- High error rates
- Database connection issues
- Memory/CPU usage
- Disk space warnings

## 🔧 Maintenance

### Regular Tasks

1. **Update base images** monthly
2. **Review security vulnerabilities** weekly
3. **Clean up unused images** weekly
4. **Backup database** daily
5. **Monitor resource usage** continuously

### Update Process

```bash
# Update base images
docker-compose pull

# Rebuild with new images
docker-compose build --no-cache

# Deploy updates
docker-compose up -d
```

This infrastructure setup provides a robust, scalable, and maintainable foundation for the fullstack monolith application.
