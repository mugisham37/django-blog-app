# Production Deployment Guide

This guide provides comprehensive instructions for deploying the fullstack monolithic application to production with enterprise-grade infrastructure, monitoring, and security.

## Overview

The production deployment includes:

- **Database Layer**: PostgreSQL with read replicas, connection pooling, and automated backups
- **Caching Layer**: Redis cluster with sentinel for high availability
- **Application Layer**: Django API and Next.js web application with load balancing
- **Security Layer**: WAF, IDS, vulnerability scanning, and comprehensive security monitoring
- **Monitoring Layer**: Prometheus, Grafana, ELK stack, and distributed tracing
- **Infrastructure**: Docker containers with Kubernetes orchestration support

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or Windows Server 2019+
- **CPU**: Minimum 8 cores (16 cores recommended)
- **Memory**: Minimum 32GB RAM (64GB recommended)
- **Storage**: Minimum 500GB SSD (1TB recommended)
- **Network**: Stable internet connection with static IP

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git 2.30+
- OpenSSL 1.1.1+
- PowerShell 7.0+ (for Windows deployment)
- Bash 4.0+ (for Linux deployment)

### Domain and SSL

- Registered domain name
- SSL certificate (Let's Encrypt or commercial)
- DNS configuration pointing to your server

## Pre-Deployment Setup

### 1. Environment Configuration

```bash
# Copy and configure environment file
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

**Critical Environment Variables:**

```bash
# Domain and SSL
DOMAIN_NAME=yourdomain.com
CERTBOT_EMAIL=admin@yourdomain.com

# Database Security
POSTGRES_PASSWORD=your_very_secure_password_here
POSTGRES_REPLICATION_PASSWORD=your_replication_password_here

# Application Security
SECRET_KEY=your_50_character_django_secret_key_here
JWT_PRIVATE_KEY=your_rsa_private_key_here
JWT_PUBLIC_KEY=your_rsa_public_key_here

# Cache Security
REDIS_PASSWORD=your_secure_redis_password_here

# Monitoring Security
ELASTIC_PASSWORD=your_elasticsearch_password_here
GRAFANA_ADMIN_PASSWORD=your_grafana_password_here
```

### 2. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com --email admin@yourdomain.com --agree-tos --non-interactive

# Copy certificates to deployment directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem infrastructure/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem infrastructure/nginx/ssl/
```

#### Option B: Commercial Certificate

```bash
# Copy your certificates
cp your-certificate.crt infrastructure/nginx/ssl/fullchain.pem
cp your-private-key.key infrastructure/nginx/ssl/privkey.pem
```

### 3. Directory Structure Setup

```bash
# Create required directories
sudo mkdir -p /opt/postgres/{primary,replica,archive,backups}
sudo mkdir -p /opt/redis/{master,replica1,replica2}
sudo mkdir -p /opt/elasticsearch/data
sudo mkdir -p /opt/grafana/data
sudo mkdir -p /opt/prometheus/data

# Set permissions
sudo chown -R 999:999 /opt/postgres/
sudo chown -R 1000:1000 /opt/redis/
sudo chown -R 1000:1000 /opt/elasticsearch/
sudo chown -R 472:472 /opt/grafana/
sudo chown -R 65534:65534 /opt/prometheus/
```

## Deployment Process

### Method 1: Automated Deployment (Recommended)

#### Linux/macOS:

```bash
# Make deployment script executable
chmod +x infrastructure/deployment/production/deploy-production.sh

# Run deployment
./infrastructure/deployment/production/deploy-production.sh --environment production --version 1.0.0
```

#### Windows:

```powershell
# Run deployment script
.\infrastructure\deployment\production\deploy-production.ps1 -Environment production -Version "1.0.0"
```

### Method 2: Manual Deployment

#### Step 1: Deploy Infrastructure Services

```bash
# Deploy database cluster
docker-compose -f infrastructure/database/production/docker-compose.prod.yml up -d

# Deploy Redis cluster
docker-compose -f infrastructure/cache/production/redis-cluster.yml up -d

# Deploy monitoring stack
docker-compose -f infrastructure/monitoring/production/performance-monitoring.yml up -d

# Deploy logging stack
docker-compose -f infrastructure/logging/production/docker-compose.logging.yml up -d

# Deploy security services
docker-compose -f infrastructure/security/production/security-config.yml up -d
```

#### Step 2: Build Application Images

```bash
# Build Django API
docker build -t django-api:1.0.0 apps/api/
docker tag django-api:1.0.0 django-api:latest

# Build Next.js Web App
docker build -t nextjs-web:1.0.0 apps/web/
docker tag nextjs-web:1.0.0 nextjs-web:latest
```

#### Step 3: Deploy Applications

```bash
# Deploy CDN and reverse proxy
docker-compose -f infrastructure/cache/production/cdn-config.yml up -d

# Deploy main application stack
docker-compose -f docker-compose.prod.yml up -d
```

#### Step 4: Run Database Migrations

```bash
# Wait for database to be ready
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-primary pg_isready -U $POSTGRES_USER

# Run migrations
docker-compose -f docker-compose.prod.yml exec django-api python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec django-api python manage.py collectstatic --noinput

# Create superuser (optional)
docker-compose -f docker-compose.prod.yml exec django-api python manage.py createsuperuser
```

## Post-Deployment Validation

### Automated Validation

```bash
# Run comprehensive validation
./infrastructure/deployment/production/deployment-validation.sh

# Check specific components
./infrastructure/deployment/production/deployment-validation.sh check-database
./infrastructure/deployment/production/deployment-validation.sh check-redis
```

### Manual Validation

#### 1. Application Health Checks

```bash
# Check main application
curl -f https://yourdomain.com/

# Check API health
curl -f https://yourdomain.com/api/health

# Check API status
curl -f https://yourdomain.com/api/v1/status
```

#### 2. Database Validation

```bash
# Check primary database
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-primary psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# Check replica
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-replica psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# Check replication status
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-primary psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM pg_stat_replication;"
```

#### 3. Cache Validation

```bash
# Check Redis master
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-master redis-cli ping

# Check Redis replicas
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-replica-1 redis-cli ping
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-replica-2 redis-cli ping

# Check sentinel status
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-sentinel-1 redis-cli -p 26379 sentinel masters
```

#### 4. Monitoring Validation

```bash
# Check Prometheus
curl -f http://localhost:9090/-/healthy

# Check Grafana
curl -f http://localhost:3001/api/health

# Check Elasticsearch
curl -f http://localhost:9200/_cluster/health

# Check Kibana
curl -f http://localhost:5601/api/status
```

## Monitoring and Alerting

### Access Monitoring Dashboards

- **Grafana**: http://localhost:3001 (admin / your_grafana_password)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601 (elastic / your_elastic_password)
- **Jaeger**: http://localhost:16686

### Key Metrics to Monitor

#### Application Metrics
- Response time and throughput
- Error rates and status codes
- Active user sessions
- API endpoint performance

#### Infrastructure Metrics
- CPU and memory utilization
- Disk space and I/O
- Network traffic and latency
- Container health and restarts

#### Database Metrics
- Connection pool usage
- Query performance and slow queries
- Replication lag
- Lock contention

#### Security Metrics
- Failed login attempts
- Suspicious IP addresses
- WAF blocked requests
- SSL certificate expiration

### Alert Configuration

Alerts are automatically configured for:

- **Critical**: Service downtime, database failures, high error rates
- **Warning**: High resource usage, slow response times, certificate expiration
- **Security**: Brute force attempts, suspicious activity, security rule violations

## Backup and Recovery

### Automated Backups

Backups are automatically configured to run daily at 2 AM:

- **Database**: Full PostgreSQL dump with compression
- **Configuration**: Environment files and Docker configurations
- **Application Data**: User uploads and media files

### Manual Backup

```bash
# Create immediate backup
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-backup /opt/backup-scripts/perform-backup.sh

# List available backups
ls -la /opt/postgres/backups/
```

### Recovery Process

```bash
# Restore from backup
./infrastructure/database/production/backup-scripts/restore-backup.sh --file /opt/postgres/backups/postgres_backup_YYYYMMDD_HHMMSS.sql.gz

# Restore from S3
./infrastructure/database/production/backup-scripts/restore-backup.sh --s3-key database-backups/postgres_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Scaling and Performance

### Horizontal Scaling

#### Scale Application Services

```bash
# Scale Django API
docker-compose -f docker-compose.prod.yml up -d --scale django-api=3

# Scale Next.js Web App
docker-compose -f docker-compose.prod.yml up -d --scale nextjs-web=2
```

#### Add Database Replicas

```bash
# Add additional read replica
docker-compose -f infrastructure/database/production/docker-compose.prod.yml up -d --scale postgres-replica=2
```

### Performance Optimization

#### Database Optimization

```sql
-- Monitor slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_distinct DESC;
```

#### Cache Optimization

```bash
# Monitor Redis performance
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-master redis-cli info stats

# Check cache hit ratio
docker-compose -f infrastructure/cache/production/redis-cluster.yml exec redis-master redis-cli info stats | grep keyspace_hits
```

## Security Hardening

### SSL/TLS Configuration

- TLS 1.2+ only
- Strong cipher suites
- HSTS headers
- Certificate pinning

### Application Security

- CSRF protection enabled
- XSS protection headers
- Content Security Policy
- Rate limiting configured

### Infrastructure Security

- Firewall rules configured
- Non-root containers
- Secret management with Vault
- Regular security updates

### Security Monitoring

- WAF logs analysis
- Intrusion detection alerts
- Vulnerability scanning reports
- Security audit logs

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check resource usage
docker stats

# Check disk space
df -h
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-primary pg_isready

# Check connection pool
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec pgbouncer psql -h localhost -p 5432 -U $POSTGRES_USER -d pgbouncer -c "SHOW POOLS;"

# Check active connections
docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec postgres-primary psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 3. High Memory Usage

```bash
# Check memory usage by container
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check system memory
free -h

# Check for memory leaks
docker-compose -f docker-compose.prod.yml exec django-api python manage.py shell -c "import gc; print(len(gc.get_objects()))"
```

#### 4. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in infrastructure/nginx/ssl/fullchain.pem -text -noout

# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
```

### Log Analysis

#### Application Logs

```bash
# Django API logs
docker-compose -f docker-compose.prod.yml logs -f django-api

# Next.js logs
docker-compose -f docker-compose.prod.yml logs -f nextjs-web

# Nginx logs
docker-compose -f infrastructure/cache/production/cdn-config.yml logs -f nginx-cdn
```

#### System Logs

```bash
# Database logs
docker-compose -f infrastructure/database/production/docker-compose.prod.yml logs -f postgres-primary

# Redis logs
docker-compose -f infrastructure/cache/production/redis-cluster.yml logs -f redis-master

# Security logs
docker-compose -f infrastructure/security/production/security-config.yml logs -f modsecurity
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health and alerts
- Review security logs
- Check backup completion

#### Weekly
- Update security rules
- Review performance metrics
- Clean up old logs and backups

#### Monthly
- Update system packages
- Review and rotate secrets
- Perform security scans
- Update SSL certificates if needed

### Update Process

#### Application Updates

```bash
# Build new version
docker build -t django-api:1.1.0 apps/api/
docker build -t nextjs-web:1.1.0 apps/web/

# Deploy with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps django-api
docker-compose -f docker-compose.prod.yml up -d --no-deps nextjs-web
```

#### Infrastructure Updates

```bash
# Update monitoring stack
docker-compose -f infrastructure/monitoring/production/performance-monitoring.yml pull
docker-compose -f infrastructure/monitoring/production/performance-monitoring.yml up -d

# Update security services
docker-compose -f infrastructure/security/production/security-config.yml pull
docker-compose -f infrastructure/security/production/security-config.yml up -d
```

## Rollback Procedures

### Automatic Rollback

The deployment script includes automatic rollback on failure:

```bash
# Deploy with automatic rollback
./infrastructure/deployment/production/deploy-production.sh --environment production --version 1.1.0
```

### Manual Rollback

```bash
# Rollback to previous version
./infrastructure/deployment/production/deploy-production.ps1 -Rollback -RollbackVersion "1.0.0"
```

### Database Rollback

```bash
# Restore database from backup
./infrastructure/database/production/backup-scripts/restore-backup.sh --file /opt/postgres/backups/pre_deployment_backup.sql.gz --force
```

## Support and Documentation

### Additional Resources

- [Architecture Documentation](../../docs/architecture/)
- [API Documentation](../../docs/api/)
- [Security Guidelines](../../docs/security/)
- [Performance Tuning Guide](../../docs/performance/)

### Getting Help

1. Check the troubleshooting section above
2. Review application and system logs
3. Check monitoring dashboards for anomalies
4. Consult the project documentation
5. Contact the development team

### Emergency Contacts

- **Critical Issues**: critical@yourdomain.com
- **Security Issues**: security@yourdomain.com
- **Database Issues**: database@yourdomain.com
- **Infrastructure Issues**: devops@yourdomain.com

---

**Note**: This production deployment guide assumes a single-server deployment. For multi-server or cloud deployments, additional configuration for load balancing, service discovery, and distributed storage may be required.