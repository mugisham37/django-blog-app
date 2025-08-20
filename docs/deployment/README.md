# Deployment Guide

This guide covers the complete deployment process for the Fullstack Monolith Transformation project, including CI/CD pipelines, rollback procedures, and disaster recovery.

## Table of Contents

1. [Overview](#overview)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Environment Setup](#environment-setup)
4. [Deployment Process](#deployment-process)
5. [Rollback Procedures](#rollback-procedures)
6. [Disaster Recovery](#disaster-recovery)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Troubleshooting](#troubleshooting)

## Overview

Our deployment strategy uses GitHub Actions for CI/CD with automated testing, security scanning, and deployment to Kubernetes clusters. We support multiple deployment strategies including rolling updates and blue-green deployments.

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │───▶│     Staging     │───▶│   Production    │
│                 │    │                 │    │                 │
│ • Feature dev   │    │ • Integration   │    │ • Live traffic  │
│ • Unit tests    │    │ • E2E tests     │    │ • Blue-green    │
│ • Code quality  │    │ • Performance   │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## CI/CD Pipeline

### Workflow Overview

1. **Continuous Integration** (`ci.yml`)
   - Code quality checks (linting, formatting, type checking)
   - Security scanning (dependencies, code, secrets)
   - Unit tests (web, API, packages)
   - Integration tests with real databases
   - End-to-end tests with Playwright
   - Performance tests with k6
   - Docker image building and pushing

2. **Staging Deployment** (`cd-staging.yml`)
   - Triggered on `develop` branch pushes
   - Database migrations
   - Rolling deployment to staging
   - Post-deployment validation
   - Automatic rollback on failure

3. **Production Deployment** (`cd-production.yml`)
   - Triggered on `main` branch pushes or releases
   - Production readiness checks
   - Security and compliance validation
   - Database backup and migration
   - Blue-green or rolling deployment
   - Comprehensive post-deployment validation

4. **Security Scanning** (`security-scan.yml`)
   - Daily automated security scans
   - Dependency vulnerability scanning
   - Code security analysis with Semgrep
   - Container security with Trivy
   - Infrastructure security with Checkov
   - License compliance checking

5. **Emergency Rollback** (`rollback.yml`)
   - Manual trigger for emergency situations
   - Application and database rollback
   - Pre-rollback backups
   - Post-rollback validation

### Pipeline Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| CI | Push to any branch, PRs | Quality assurance |
| Staging Deploy | Push to `develop` | Integration testing |
| Production Deploy | Push to `main`, releases | Production deployment |
| Security Scan | Daily schedule, manual | Security monitoring |
| Rollback | Manual only | Emergency recovery |

## Environment Setup

### Prerequisites

1. **GitHub Secrets Configuration**
   ```bash
   # Kubernetes configurations
   KUBE_CONFIG_STAGING      # Base64 encoded kubeconfig for staging
   KUBE_CONFIG_PRODUCTION   # Base64 encoded kubeconfig for production
   
   # Container registry
   GITHUB_TOKEN             # For GitHub Container Registry
   
   # Monitoring and alerting
   GRAFANA_PASSWORD         # Grafana admin password
   SENTRY_DSN              # Error tracking
   ```

2. **Kubernetes Cluster Setup**
   ```bash
   # Create namespaces
   kubectl create namespace fullstack-staging
   kubectl create namespace fullstack-production
   
   # Apply RBAC and network policies
   kubectl apply -f infrastructure/k8s/rbac/
   kubectl apply -f infrastructure/k8s/network-policies/
   ```

3. **Database Setup**
   ```bash
   # Create database secrets
   kubectl create secret generic postgres-secret \
     --from-literal=password=your-secure-password \
     --namespace=fullstack-staging
   
   kubectl create secret generic django-secret \
     --from-literal=secret-key=your-django-secret \
     --from-literal=database-url=postgresql://... \
     --namespace=fullstack-staging
   ```

### Environment Variables

#### Staging Environment
```bash
# API Configuration
DATABASE_URL=postgresql://user:pass@postgres:5432/staging_db
REDIS_URL=redis://redis:6379/0
DEBUG=0
ALLOWED_HOSTS=api-staging.yourapp.com

# Web Configuration
NEXT_PUBLIC_API_URL=https://api-staging.yourapp.com
NEXTAUTH_URL=https://staging.yourapp.com
```

#### Production Environment
```bash
# API Configuration
DATABASE_URL=postgresql://user:pass@postgres:5432/production_db
REDIS_URL=redis://redis:6379/0
DEBUG=0
ALLOWED_HOSTS=api.yourapp.com

# Web Configuration
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXTAUTH_URL=https://yourapp.com
```

## Deployment Process

### Automatic Deployment

1. **Development to Staging**
   ```bash
   # Push to develop branch triggers staging deployment
   git checkout develop
   git merge feature/your-feature
   git push origin develop
   ```

2. **Staging to Production**
   ```bash
   # Create release or push to main
   git checkout main
   git merge develop
   git push origin main
   
   # Or create a release
   gh release create v1.2.3 --title "Release v1.2.3" --notes "Release notes"
   ```

### Manual Deployment

1. **Trigger Staging Deployment**
   ```bash
   # Using GitHub CLI
   gh workflow run "Deploy to Staging" --ref develop
   
   # Or via GitHub UI: Actions → Deploy to Staging → Run workflow
   ```

2. **Trigger Production Deployment**
   ```bash
   # Using GitHub CLI
   gh workflow run "Deploy to Production" --ref main \
     -f environment=production \
     -f skip_tests=false
   ```

### Deployment Strategies

#### Rolling Deployment (Default)
- Gradual replacement of old pods with new ones
- Zero-downtime deployment
- Automatic rollback on health check failures

#### Blue-Green Deployment
- Deploy to inactive environment (blue/green)
- Switch traffic after validation
- Instant rollback capability
- Used for major releases

### Database Migrations

Migrations are handled automatically during deployment:

1. **Pre-deployment Backup**
   - Automatic database backup before migrations
   - Stored in persistent volumes with retention policy

2. **Migration Execution**
   - Dry-run validation in separate job
   - Actual migration with timeout and retry logic
   - Rollback capability for failed migrations

3. **Post-migration Validation**
   - Data integrity checks
   - Application health verification

## Rollback Procedures

### Automatic Rollback

Automatic rollback is triggered when:
- Health checks fail after deployment
- Post-deployment tests fail
- Performance thresholds are exceeded

### Manual Rollback

1. **Emergency Rollback**
   ```bash
   # Trigger emergency rollback workflow
   gh workflow run "Emergency Rollback" \
     -f environment=production \
     -f rollback_type=full \
     -f reason="Critical bug in payment processing"
   ```

2. **Application-Only Rollback**
   ```bash
   # Rollback just the application (not database)
   gh workflow run "Emergency Rollback" \
     -f environment=production \
     -f rollback_type=deployment \
     -f reason="UI regression"
   ```

3. **Database Rollback**
   ```bash
   # Rollback database to previous state
   gh workflow run "Emergency Rollback" \
     -f environment=production \
     -f rollback_type=database \
     -f reason="Data corruption detected"
   ```

### Rollback Process

1. **Pre-rollback Backup**
   - Current state backup before rollback
   - Ensures ability to roll forward if needed

2. **Application Rollback**
   - Kubernetes deployment rollback to previous revision
   - Service mesh traffic routing updates

3. **Database Rollback** (if needed)
   - Application shutdown to prevent connections
   - Database restore from backup
   - Application restart with validation

4. **Validation**
   - Health checks and smoke tests
   - Performance validation
   - User acceptance testing

## Disaster Recovery

### Backup Strategy

1. **Database Backups**
   - Automated daily backups
   - Point-in-time recovery capability
   - Cross-region backup replication
   - 30-day retention policy

2. **Application State**
   - Container images stored in registry
   - Configuration stored in Git
   - Secrets backed up securely

3. **Infrastructure as Code**
   - Kubernetes manifests in Git
   - Terraform/Helm charts versioned
   - Complete environment reproducibility

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Restore from specific backup
   kubectl apply -f infrastructure/k8s/jobs/restore-job.yaml
   
   # Monitor restoration progress
   kubectl logs -f job/database-restore-$(date +%Y%m%d)
   ```

2. **Full Environment Recovery**
   ```bash
   # Recreate entire environment
   kubectl apply -f infrastructure/k8s/
   
   # Restore database
   kubectl apply -f infrastructure/k8s/jobs/restore-job.yaml
   
   # Deploy latest application
   gh workflow run "Deploy to Production" --ref main
   ```

### Recovery Time Objectives (RTO)

| Component | RTO | RPO |
|-----------|-----|-----|
| Application | 15 minutes | 0 (stateless) |
| Database | 30 minutes | 1 hour |
| Full Environment | 60 minutes | 1 hour |

## Monitoring and Alerting

### Health Checks

1. **Application Health**
   - `/health/` endpoint monitoring
   - Kubernetes liveness/readiness probes
   - Response time and error rate tracking

2. **Database Health**
   - Connection pool monitoring
   - Query performance tracking
   - Replication lag monitoring

3. **Infrastructure Health**
   - Node resource utilization
   - Network connectivity
   - Storage capacity

### Alerting Rules

1. **Critical Alerts** (Immediate Response)
   - Application down (>5 minutes)
   - Database connection failures
   - High error rates (>5%)
   - Security incidents

2. **Warning Alerts** (Response within 1 hour)
   - High response times (>2 seconds)
   - Resource utilization (>80%)
   - Failed deployments
   - Performance degradation

3. **Info Alerts** (Response within 24 hours)
   - Dependency updates available
   - Security scan results
   - Performance reports

### Monitoring Dashboards

1. **Application Dashboard**
   - Request rates and response times
   - Error rates and status codes
   - User activity and sessions

2. **Infrastructure Dashboard**
   - CPU, memory, and disk usage
   - Network traffic and latency
   - Kubernetes cluster health

3. **Business Dashboard**
   - User registrations and activity
   - Feature usage analytics
   - Performance KPIs

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   ```bash
   # Check deployment status
   kubectl rollout status deployment/django-api -n fullstack-production
   
   # View pod logs
   kubectl logs -l app=django-api -n fullstack-production --tail=100
   
   # Describe deployment for events
   kubectl describe deployment django-api -n fullstack-production
   ```

2. **Database Connection Issues**
   ```bash
   # Check database pod status
   kubectl get pods -l app=postgres -n fullstack-production
   
   # Test database connectivity
   kubectl exec -it deployment/django-api -n fullstack-production -- \
     python manage.py dbshell
   ```

3. **Performance Issues**
   ```bash
   # Check resource usage
   kubectl top pods -n fullstack-production
   
   # View application metrics
   curl https://api.yourapp.com/metrics
   
   # Check database performance
   kubectl exec -it postgres-pod -- psql -c "SELECT * FROM pg_stat_activity;"
   ```

### Debug Commands

```bash
# Get all resources in namespace
kubectl get all -n fullstack-production

# Check events for issues
kubectl get events -n fullstack-production --sort-by='.lastTimestamp'

# Port forward for local debugging
kubectl port-forward service/django-api 8000:8000 -n fullstack-production

# Execute commands in pods
kubectl exec -it deployment/django-api -n fullstack-production -- bash

# View logs with timestamps
kubectl logs deployment/django-api -n fullstack-production --timestamps=true
```

### Emergency Contacts

| Role | Contact | Escalation Time |
|------|---------|----------------|
| DevOps Engineer | devops@yourapp.com | Immediate |
| Site Reliability Engineer | sre@yourapp.com | 15 minutes |
| Technical Lead | tech-lead@yourapp.com | 30 minutes |
| Engineering Manager | eng-manager@yourapp.com | 1 hour |

### Support Procedures

1. **Incident Response**
   - Create incident in monitoring system
   - Notify relevant stakeholders
   - Begin troubleshooting and resolution
   - Document actions and outcomes

2. **Post-Incident Review**
   - Root cause analysis
   - Process improvements
   - Documentation updates
   - Prevention measures

For more detailed information, see:
- [CI/CD Pipeline Configuration](./cicd-pipeline.md)
- [Security and Compliance](./security-compliance.md)
- [Performance Monitoring](./performance-monitoring.md)
- [Disaster Recovery Plan](./disaster-recovery.md)