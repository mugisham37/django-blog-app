# Database Infrastructure

This directory contains comprehensive database infrastructure for the enterprise application, including PostgreSQL with read replicas, connection pooling, monitoring, backup/restore, and performance optimization.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   PgBouncer     │    │   PostgreSQL    │
│   Services      │───▶│   Connection    │───▶│   Primary       │
│                 │    │   Pooler        │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   PostgreSQL    │
                                               │   Read Replica  │
                                               │                 │
                                               └─────────────────┘
```

## 📁 Directory Structure

```
infrastructure/database/
├── README.md                           # This documentation
├── docker-compose.database.yml         # Docker services configuration
├── manage.py                          # Database management CLI
├── migrate.py                         # Migration management tool
├── seed.py                           # Data seeding tool
├── backup.sh                         # Backup script
├── restore.sh                        # Restore script
├── setup-replica.sh                  # Replica setup script
├── postgresql.conf                   # PostgreSQL primary configuration
├── postgresql-replica.conf           # PostgreSQL replica configuration
├── pg_hba.conf                      # PostgreSQL authentication
├── pgbouncer.ini                    # PgBouncer configuration
├── userlist.txt                     # PgBouncer user authentication
├── Dockerfile.pgbouncer             # PgBouncer Docker image
├── init.sql                         # Database initialization
├── migrations/                      # Database migrations
│   ├── 001_initial_schema.sql
│   └── rollback_001.sql
├── seeds/                          # Data seeding scripts
│   ├── development_seed.sql
│   ├── production_seed.sql
│   └── test_seed.sql
├── monitoring/                     # Performance monitoring
│   ├── slow_queries.sql
│   └── performance_monitor.py
└── tests/                         # Database tests
    └── performance_tests.py
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- PostgreSQL client tools (optional, for direct access)

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_DB=enterprise_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432
POSTGRES_REPLICA_PORT=5433

# Connection Pooling
PGBOUNCER_PORT=6432

# Redis Configuration
REDIS_PORT=6379
REDIS_SENTINEL_PORT=26379

# Backup Configuration
BACKUP_RETENTION_DAYS=30
S3_BACKUP_BUCKET=your-backup-bucket
SLACK_WEBHOOK=your-slack-webhook-url

# Admin Tools
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin_password
PGADMIN_PORT=8080
```

### 2. Development Environment

```bash
# Setup development environment (includes seeding)
python infrastructure/database/manage.py setup-dev

# Or manually start services
python infrastructure/database/manage.py start --profiles monitoring

# Check status
python infrastructure/database/manage.py status

# View logs
python infrastructure/database/manage.py logs --follow
```

### 3. Production Environment

```bash
# Setup production environment
python infrastructure/database/manage.py setup-prod

# Start with all production services
python infrastructure/database/manage.py start --profiles monitoring backup
```

## 🛠️ Database Management

### Migration Management

```bash
# Check migration status
python infrastructure/database/manage.py migrate status

# Apply all pending migrations
python infrastructure/database/manage.py migrate up

# Rollback to specific version
python infrastructure/database/manage.py migrate down 001

# Create new migration
python infrastructure/database/migrate.py --db-url "postgresql://..." create "Add user preferences table"
```

### Data Seeding

```bash
# Seed development data
python infrastructure/database/manage.py seed development

# Seed production data
python infrastructure/database/manage.py seed production

# Seed test data
python infrastructure/database/manage.py seed test
```

### Backup and Restore

```bash
# Create backup
python infrastructure/database/manage.py backup --output backup_$(date +%Y%m%d).sql

# Restore from backup
python infrastructure/database/manage.py restore backup_20231201.sql

# Automated backups (runs via cron in backup container)
# Configured in docker-compose.database.yml
```

### Performance Monitoring

```bash
# Run performance tests
python infrastructure/database/manage.py performance --output perf_results.json

# Monitor performance continuously
python infrastructure/database/manage.py monitor --duration 3600

# Check slow queries
python infrastructure/database/manage.py sql "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## 🔧 Configuration

### PostgreSQL Configuration

The database is configured for production use with:

- **Connection pooling** via PgBouncer (25 connections per pool)
- **Read replicas** for read scaling
- **WAL archiving** for point-in-time recovery
- **Performance tuning** for medium-sized deployments
- **Monitoring** with pg_stat_statements
- **Audit logging** for security compliance

### Key Configuration Files

- `postgresql.conf`: Primary database configuration
- `postgresql-replica.conf`: Read replica configuration
- `pgbouncer.ini`: Connection pooler settings
- `pg_hba.conf`: Authentication rules

### Performance Tuning

Current settings are optimized for:

- **Memory**: 256MB shared_buffers, 1GB effective_cache_size
- **Connections**: 200 max connections, pooled via PgBouncer
- **WAL**: Replica level for replication support
- **Checkpoints**: 90% completion target for smooth I/O

## 📊 Monitoring and Observability

### Built-in Monitoring

1. **PostgreSQL Exporter**: Metrics for Prometheus
2. **Redis Exporter**: Cache metrics
3. **Performance Monitor**: Custom Python monitoring
4. **Slow Query Analysis**: Automated query performance tracking

### Health Checks

```bash
# Comprehensive health check
python infrastructure/database/manage.py health

# Individual service checks
docker-compose -f infrastructure/database/docker-compose.database.yml ps
```

### Key Metrics to Monitor

- Connection count and pool utilization
- Query execution times and slow queries
- Cache hit ratios (buffer cache, index cache)
- Replication lag
- Disk I/O and space usage
- Lock contention

## 🔒 Security Features

### Authentication and Authorization

- **Role-based access control** (RBAC) system
- **Audit logging** for all data changes
- **Password encryption** with bcrypt
- **Connection security** with SSL support (configurable)

### Security Best Practices

1. **Principle of least privilege**: Users have minimal required permissions
2. **Audit trails**: All changes are logged with user attribution
3. **Secure defaults**: Production-ready security configuration
4. **Regular backups**: Automated backup with retention policies

## 🧪 Testing

### Performance Testing

```bash
# Run comprehensive performance tests
python infrastructure/database/tests/performance_tests.py --db-url "postgresql://..."

# Test specific scenarios
python infrastructure/database/tests/performance_tests.py --db-url "..." --threads 20
```

### Test Coverage

- Connection performance
- Query execution times
- Concurrent read/write operations
- Bulk operations
- Index effectiveness
- Transaction performance

## 🚨 Troubleshooting

### Common Issues

#### Connection Issues

```bash
# Check if services are running
python infrastructure/database/manage.py status

# Check logs for errors
python infrastructure/database/manage.py logs postgres-primary

# Test direct connection
psql -h localhost -p 5432 -U postgres -d enterprise_db
```

#### Performance Issues

```bash
# Check slow queries
python infrastructure/database/manage.py sql "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Monitor active connections
python infrastructure/database/manage.py sql "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check cache hit ratio
python infrastructure/database/manage.py sql "SELECT sum(blks_hit)*100/sum(blks_hit+blks_read) as hit_ratio FROM pg_stat_database;"
```

#### Replication Issues

```bash
# Check replication status
python infrastructure/database/manage.py sql "SELECT * FROM pg_stat_replication;"

# Check replica lag
docker-compose -f infrastructure/database/docker-compose.database.yml exec postgres-replica psql -U postgres -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;"
```

### Log Locations

- PostgreSQL logs: Available via `docker-compose logs postgres-primary`
- PgBouncer logs: Available via `docker-compose logs pgbouncer`
- Application logs: Structured JSON format with rotation

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Read Replicas**: Add more read replicas for read-heavy workloads
2. **Connection Pooling**: Increase PgBouncer pool sizes
3. **Sharding**: Consider partitioning for very large datasets

### Vertical Scaling

1. **Memory**: Increase shared_buffers and effective_cache_size
2. **CPU**: Adjust max_worker_processes and parallel query settings
3. **Storage**: Use faster SSDs and increase checkpoint_segments

### Monitoring Scaling Needs

- Monitor connection pool utilization
- Track query response times
- Watch for I/O bottlenecks
- Monitor replication lag

## 🔄 Maintenance

### Regular Maintenance Tasks

1. **Vacuum and Analyze**: Automated via autovacuum
2. **Index Maintenance**: Monitor unused indexes
3. **Log Rotation**: Automated with retention policies
4. **Backup Verification**: Regular restore testing
5. **Security Updates**: Keep PostgreSQL version current

### Maintenance Commands

```bash
# Manual vacuum (if needed)
python infrastructure/database/manage.py sql "VACUUM ANALYZE;"

# Reindex if needed
python infrastructure/database/manage.py sql "REINDEX DATABASE enterprise_db;"

# Update statistics
python infrastructure/database/manage.py sql "ANALYZE;"
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PgBouncer Documentation](https://www.pgbouncer.org/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Database Security Best Practices](https://www.postgresql.org/docs/current/security.html)

## 🤝 Contributing

When making changes to the database infrastructure:

1. Test changes in development environment first
2. Update migration scripts for schema changes
3. Update seed data if needed
4. Run performance tests to ensure no regressions
5. Update documentation for configuration changes

## 📄 License

This database infrastructure is part of the enterprise application and follows the same licensing terms.
