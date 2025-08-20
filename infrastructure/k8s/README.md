# Kubernetes Infrastructure

This directory contains the complete Kubernetes orchestration configuration for the fullstack monolith application, providing production-ready deployment, scaling, and management capabilities.

## 📁 Directory Structure

```
infrastructure/k8s/
├── base/                           # Base Kubernetes manifests
│   ├── configmap.yaml             # Application configuration
│   ├── django-deployment.yaml     # Django API deployment
│   ├── hpa.yaml                   # Horizontal Pod Autoscaler
│   ├── ingress.yaml               # Ingress controller configuration
│   ├── kustomization.yaml         # Base kustomization
│   ├── monitoring.yaml            # Monitoring configuration
│   ├── namespace.yaml             # Namespace definitions
│   ├── nextjs-deployment.yaml     # Next.js web deployment
│   ├── nginx-deployment.yaml      # Nginx proxy deployment
│   ├── persistent-volumes.yaml    # Storage configuration
│   ├── postgres-deployment.yaml   # PostgreSQL database
│   ├── redis-deployment.yaml      # Redis cache
│   └── secrets.yaml               # Secret management
├── overlays/                      # Environment-specific configurations
│   ├── development/               # Development environment
│   ├── staging/                   # Staging environment
│   └── production/                # Production environment
└── scripts/                       # Deployment and management scripts
    ├── deploy.ps1                 # PowerShell deployment script
    ├── deploy.sh                  # Bash deployment script
    ├── rollback.ps1               # Rollback management
    ├── test-deployment.ps1        # Deployment testing
    └── validate.ps1               # Configuration validation
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured and connected to your cluster
- kustomize (v4.0+)
- PowerShell 7+ (for PowerShell scripts) or Bash (for shell scripts)

### Deploy to Development

```powershell
# Using PowerShell
.\infrastructure\k8s\scripts\deploy.ps1 -Environment development

# Using Bash
./infrastructure/k8s/scripts/deploy.sh -e development
```

### Deploy to Production

```powershell
# Using PowerShell
.\infrastructure\k8s\scripts\deploy.ps1 -Environment production -ImageTag v1.0.0

# Using Bash
./infrastructure/k8s/scripts/deploy.sh -e production -t v1.0.0
```

## 🏗️ Architecture Overview

### Components

1. **Django API** - Backend REST API with Celery workers
2. **Next.js Web** - Frontend React application
3. **PostgreSQL** - Primary database with persistent storage
4. **Redis** - Caching and message broker
5. **Nginx** - Reverse proxy and load balancer
6. **Monitoring** - Prometheus metrics and health checks

### Networking

- **Ingress Controller** - Routes external traffic to services
- **Network Policies** - Secure inter-pod communication
- **Service Mesh** - Load balancing and service discovery

### Storage

- **Persistent Volumes** - Database and media file storage
- **ConfigMaps** - Application configuration
- **Secrets** - Sensitive data management

## 🌍 Environment Configurations

### Development

- **Replicas**: 1 per service (resource efficient)
- **Resources**: Minimal CPU/memory allocation
- **Storage**: 2Gi PostgreSQL, 1Gi Redis
- **Features**: Debug mode enabled, relaxed security

### Staging

- **Replicas**: 2 per service (basic HA)
- **Resources**: Moderate CPU/memory allocation
- **Storage**: 20Gi PostgreSQL, 5Gi Redis
- **Features**: Production-like configuration for testing

### Production

- **Replicas**: 5+ per service (high availability)
- **Resources**: Optimized CPU/memory allocation
- **Storage**: 100Gi PostgreSQL, 20Gi Redis
- **Features**: Full security, monitoring, and scaling

## 📊 Scaling and High Availability

### Horizontal Pod Autoscaler (HPA)

Automatic scaling based on:

- CPU utilization (60-70% target)
- Memory utilization (70-80% target)
- Custom metrics (request rate, queue length)

```yaml
# Example HPA configuration
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

### Pod Anti-Affinity

Ensures pods are distributed across nodes:

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values: [django-api]
          topologyKey: kubernetes.io/hostname
```

## 🔒 Security Features

### Network Security

- Network policies restrict inter-pod communication
- Ingress with TLS termination
- Security headers and rate limiting

### Container Security

- Non-root user execution
- Read-only root filesystems where possible
- Security contexts and capabilities

### Secret Management

- Kubernetes secrets for sensitive data
- Separate secrets per environment
- Automatic secret rotation support

## 📈 Monitoring and Observability

### Prometheus Integration

- ServiceMonitor configurations
- Custom metrics collection
- Alerting rules for critical issues

### Health Checks

- Liveness probes for container health
- Readiness probes for traffic routing
- Startup probes for slow-starting containers

### Logging

- Structured logging with JSON format
- Log aggregation ready
- Error tracking integration

## 🛠️ Management Scripts

### Deployment Script

```powershell
# Deploy with validation
.\scripts\deploy.ps1 -Environment production -ImageTag v1.2.3 -WaitForReady

# Dry run deployment
.\scripts\deploy.ps1 -Environment staging -DryRun
```

### Rollback Script

```powershell
# Rollback to previous version
.\scripts\rollback.ps1 -Environment production -Component django-api

# Rollback to specific revision
.\scripts\rollback.ps1 -Environment production -Component all -Revision 5

# Interactive rollback
.\scripts\rollback.ps1 -Environment staging -Component interactive
```

### Validation Script

```powershell
# Validate configuration
.\scripts\validate.ps1 -Environment production

# Verbose validation
.\scripts\validate.ps1 -Environment development -Verbose
```

### Testing Script

```powershell
# Test deployment health
.\scripts\test-deployment.ps1 -Environment production

# Skip load testing
.\scripts\test-deployment.ps1 -Environment staging -SkipLoadTest
```

## 🔧 Configuration Management

### Kustomize Structure

Base configurations are extended by environment-specific overlays:

```yaml
# Base kustomization.yaml
resources:
  - namespace.yaml
  - configmap.yaml
  - secrets.yaml
  - deployments/
  - services/
  - ingress.yaml

# Environment overlay
patchesStrategicMerge:
  - django-prod-patch.yaml
  - nextjs-prod-patch.yaml

configMapGenerator:
  - name: prod-config
    behavior: merge
    literals:
      - DEBUG=False
      - LOG_LEVEL=INFO
```

### Environment Variables

Configuration is managed through:

- **ConfigMaps** - Non-sensitive configuration
- **Secrets** - Sensitive data (passwords, keys)
- **Environment-specific patches** - Override base values

## 🚨 Troubleshooting

### Common Issues

1. **Pod Startup Failures**

   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   kubectl logs <pod-name> -n <namespace>
   ```

2. **Service Connectivity**

   ```bash
   kubectl get endpoints -n <namespace>
   kubectl port-forward service/<service-name> 8080:80
   ```

3. **Resource Constraints**
   ```bash
   kubectl top pods -n <namespace>
   kubectl describe nodes
   ```

### Health Check Endpoints

- Django API: `GET /health/`
- Next.js Web: `GET /api/health`
- Nginx Proxy: `GET /health`

### Log Analysis

```bash
# View application logs
kubectl logs -f deployment/django-api -n fullstack-monolith-prod

# View previous container logs
kubectl logs deployment/django-api -n fullstack-monolith-prod --previous

# Follow logs from multiple pods
kubectl logs -f -l app=django-api -n fullstack-monolith-prod
```

## 🔄 Rolling Updates

### Deployment Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 2
    maxUnavailable: 1
```

### Update Process

1. **Build and tag new image**
2. **Update image tag in overlay**
3. **Deploy with validation**
4. **Monitor rollout status**
5. **Verify health checks**
6. **Rollback if issues detected**

### Rollback Procedures

```powershell
# Quick rollback to previous version
kubectl rollout undo deployment/django-api -n fullstack-monolith-prod

# Rollback to specific revision
kubectl rollout undo deployment/django-api -n fullstack-monolith-prod --to-revision=3

# Check rollout status
kubectl rollout status deployment/django-api -n fullstack-monolith-prod
```

## 📋 Maintenance Tasks

### Regular Maintenance

1. **Update base images** - Monthly security updates
2. **Review resource usage** - Optimize requests/limits
3. **Clean up old revisions** - Manage deployment history
4. **Update certificates** - Renew TLS certificates
5. **Backup validation** - Test restore procedures

### Scaling Operations

```bash
# Manual scaling
kubectl scale deployment django-api --replicas=10 -n fullstack-monolith-prod

# Update HPA limits
kubectl patch hpa django-api-hpa -p '{"spec":{"maxReplicas":15}}' -n fullstack-monolith-prod
```

## 🔐 Security Best Practices

### Cluster Security

- RBAC policies for service accounts
- Pod Security Standards enforcement
- Network segmentation with policies
- Regular security scanning

### Application Security

- Non-privileged containers
- Immutable container filesystems
- Secret rotation procedures
- Vulnerability scanning in CI/CD

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Ingress NGINX Controller](https://kubernetes.github.io/ingress-nginx/)

## 🤝 Contributing

When modifying Kubernetes configurations:

1. **Test in development first**
2. **Validate with scripts before applying**
3. **Update documentation for changes**
4. **Follow security best practices**
5. **Test rollback procedures**

## 📞 Support

For issues with Kubernetes deployments:

1. Check the troubleshooting section
2. Review pod logs and events
3. Validate configuration syntax
4. Test in lower environments first
5. Contact the platform team for cluster issues
