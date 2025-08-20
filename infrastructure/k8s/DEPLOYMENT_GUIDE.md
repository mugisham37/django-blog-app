# Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying the fullstack monolith application to Kubernetes across different environments.

## 📋 Prerequisites

### Required Tools

1. **kubectl** (v1.24+)

   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   ```

2. **kustomize** (v4.0+)

   ```bash
   # Install kustomize
   curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
   sudo mv kustomize /usr/local/bin/
   ```

3. **PowerShell** 7+ (for PowerShell scripts)
   ```bash
   # Install PowerShell on Linux
   wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
   sudo dpkg -i packages-microsoft-prod.deb
   sudo apt-get update
   sudo apt-get install -y powershell
   ```

### Cluster Requirements

- **Kubernetes Version**: 1.24 or higher
- **Node Resources**: Minimum 4 CPU cores, 8GB RAM per node
- **Storage**: Dynamic provisioning or pre-created persistent volumes
- **Ingress Controller**: NGINX Ingress Controller recommended
- **Monitoring**: Prometheus Operator (optional but recommended)

### Access Requirements

- Cluster admin access for initial setup
- Namespace admin access for application deployment
- Container registry access for image pulling

## 🚀 Initial Cluster Setup

### 1. Create Namespaces

```bash
kubectl apply -f infrastructure/k8s/base/namespace.yaml
```

### 2. Install Ingress Controller (if not present)

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### 3. Install Prometheus Operator (optional)

```bash
# Install Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

### 4. Create Storage Classes

```bash
kubectl apply -f infrastructure/k8s/base/storage-classes.yaml
```

## 🏗️ Environment-Specific Deployments

### Development Environment

#### 1. Prepare Configuration

```bash
# Navigate to project root
cd /path/to/your/project

# Validate configuration
./infrastructure/k8s/scripts/validate.ps1 -Environment development
```

#### 2. Deploy Application

```bash
# Deploy using PowerShell script
./infrastructure/k8s/scripts/deploy.ps1 -Environment development

# Or deploy using Bash script
./infrastructure/k8s/scripts/deploy.sh -e development

# Or deploy manually with kustomize
kubectl apply -k infrastructure/k8s/overlays/development
```

#### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n fullstack-monolith-dev

# Check services
kubectl get services -n fullstack-monolith-dev

# Run deployment tests
./infrastructure/k8s/scripts/test-deployment.ps1 -Environment development
```

#### 4. Access Application

```bash
# Port forward to access locally
kubectl port-forward service/dev-nextjs-web-service 3000:3000 -n fullstack-monolith-dev
kubectl port-forward service/dev-django-api-service 8000:8000 -n fullstack-monolith-dev

# Access at:
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Staging Environment

#### 1. Build and Tag Images

```bash
# Build production images
docker build -t your-registry/django-api:staging-v1.0.0 apps/api/
docker build -t your-registry/nextjs-web:staging-v1.0.0 apps/web/

# Push to registry
docker push your-registry/django-api:staging-v1.0.0
docker push your-registry/nextjs-web:staging-v1.0.0
```

#### 2. Update Image Tags

```bash
# Update kustomization.yaml with new image tags
cd infrastructure/k8s/overlays/staging
```

Edit `kustomization.yaml`:

```yaml
images:
  - name: django-api
    newTag: staging-v1.0.0
  - name: nextjs-web
    newTag: staging-v1.0.0
```

#### 3. Deploy to Staging

```bash
# Deploy with specific image tag
./infrastructure/k8s/scripts/deploy.ps1 -Environment staging -ImageTag staging-v1.0.0

# Wait for deployment to complete
kubectl rollout status deployment/staging-django-api -n fullstack-monolith-staging
kubectl rollout status deployment/staging-nextjs-web -n fullstack-monolith-staging
```

#### 4. Run Integration Tests

```bash
# Run comprehensive tests
./infrastructure/k8s/scripts/test-deployment.ps1 -Environment staging

# Check application health
kubectl get pods -n fullstack-monolith-staging
kubectl logs -f deployment/staging-django-api -n fullstack-monolith-staging
```

### Production Environment

#### 1. Pre-Deployment Checklist

- [ ] Images built and tested in staging
- [ ] Database migrations reviewed
- [ ] Secrets updated with production values
- [ ] Monitoring and alerting configured
- [ ] Backup procedures verified
- [ ] Rollback plan prepared

#### 2. Update Production Secrets

```bash
# Create production secrets (replace with actual values)
kubectl create secret generic prod-secrets \
  --from-literal=SECRET_KEY="your-production-secret-key" \
  --from-literal=POSTGRES_PASSWORD="your-production-db-password" \
  --from-literal=REDIS_PASSWORD="your-production-redis-password" \
  --from-literal=JWT_SECRET_KEY="your-production-jwt-secret" \
  --namespace=fullstack-monolith-prod \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### 3. Deploy to Production

```bash
# Deploy with production safety checks
./infrastructure/k8s/scripts/deploy.ps1 -Environment production -ImageTag v1.0.0 -WaitForReady

# Monitor deployment progress
kubectl rollout status deployment/prod-django-api -n fullstack-monolith-prod --timeout=600s
kubectl rollout status deployment/prod-nextjs-web -n fullstack-monolith-prod --timeout=600s
```

#### 4. Post-Deployment Verification

```bash
# Run production health checks
./infrastructure/k8s/scripts/test-deployment.ps1 -Environment production

# Verify all services are healthy
kubectl get pods -n fullstack-monolith-prod
kubectl get services -n fullstack-monolith-prod
kubectl get ingress -n fullstack-monolith-prod

# Check HPA status
kubectl get hpa -n fullstack-monolith-prod
```

## 🔄 Rolling Updates

### Standard Rolling Update

```bash
# Update image tag in overlay
cd infrastructure/k8s/overlays/production

# Edit kustomization.yaml to update image tag
# Then deploy
./infrastructure/k8s/scripts/deploy.ps1 -Environment production -ImageTag v1.1.0
```

### Blue-Green Deployment (Manual)

```bash
# 1. Deploy new version with different label
kubectl patch deployment prod-django-api -p '{"spec":{"selector":{"matchLabels":{"version":"v1.1.0"}},"template":{"metadata":{"labels":{"version":"v1.1.0"}}}}}' -n fullstack-monolith-prod

# 2. Wait for new pods to be ready
kubectl rollout status deployment/prod-django-api -n fullstack-monolith-prod

# 3. Update service selector to new version
kubectl patch service prod-django-api-service -p '{"spec":{"selector":{"version":"v1.1.0"}}}' -n fullstack-monolith-prod

# 4. Clean up old deployment if successful
```

### Canary Deployment

```bash
# 1. Create canary deployment
kubectl create deployment prod-django-api-canary --image=django-api:v1.1.0 -n fullstack-monolith-prod

# 2. Scale canary to small percentage
kubectl scale deployment prod-django-api-canary --replicas=1 -n fullstack-monolith-prod

# 3. Update service to include canary pods
kubectl patch service prod-django-api-service -p '{"spec":{"selector":{"app":"django-api"}}}' -n fullstack-monolith-prod

# 4. Monitor metrics and gradually increase canary traffic
# 5. Replace main deployment if successful
```

## 🚨 Rollback Procedures

### Quick Rollback

```bash
# Rollback to previous version
./infrastructure/k8s/scripts/rollback.ps1 -Environment production -Component django-api

# Rollback all components
./infrastructure/k8s/scripts/rollback.ps1 -Environment production -Component all
```

### Rollback to Specific Version

```bash
# List available revisions
kubectl rollout history deployment/prod-django-api -n fullstack-monolith-prod

# Rollback to specific revision
./infrastructure/k8s/scripts/rollback.ps1 -Environment production -Component django-api -Revision 3
```

### Emergency Rollback

```bash
# Force rollback without confirmation (use with caution)
./infrastructure/k8s/scripts/rollback.ps1 -Environment production -Component all -Force

# Scale down problematic deployment immediately
kubectl scale deployment prod-django-api --replicas=0 -n fullstack-monolith-prod
```

## 🔧 Configuration Management

### Environment Variables

Update configuration through ConfigMaps:

```bash
# Update development config
kubectl patch configmap dev-config -p '{"data":{"DEBUG":"True","LOG_LEVEL":"DEBUG"}}' -n fullstack-monolith-dev

# Update production config
kubectl patch configmap prod-config -p '{"data":{"LOG_LEVEL":"INFO","ALLOWED_HOSTS":"yourdomain.com"}}' -n fullstack-monolith-prod
```

### Secrets Management

```bash
# Update database password
kubectl patch secret database-secret -p '{"data":{"POSTGRES_PASSWORD":"'$(echo -n "new-password" | base64)'"}}' -n fullstack-monolith-prod

# Restart deployments to pick up new secrets
kubectl rollout restart deployment/prod-django-api -n fullstack-monolith-prod
```

### Feature Flags

```bash
# Enable/disable features through ConfigMap
kubectl patch configmap django-config -p '{"data":{"FEATURE_NEW_UI":"true","FEATURE_ANALYTICS":"false"}}' -n fullstack-monolith-prod
```

## 📊 Monitoring and Logging

### View Logs

```bash
# View application logs
kubectl logs -f deployment/prod-django-api -n fullstack-monolith-prod

# View logs from all pods
kubectl logs -f -l app=django-api -n fullstack-monolith-prod

# View previous container logs
kubectl logs deployment/prod-django-api --previous -n fullstack-monolith-prod
```

### Monitor Resources

```bash
# Check resource usage
kubectl top pods -n fullstack-monolith-prod
kubectl top nodes

# Check HPA metrics
kubectl describe hpa prod-django-api-hpa -n fullstack-monolith-prod
```

### Access Metrics

```bash
# Port forward to Prometheus (if installed)
kubectl port-forward service/prometheus-operated 9090:9090 -n monitoring

# Port forward to Grafana (if installed)
kubectl port-forward service/grafana 3000:3000 -n monitoring
```

## 🛠️ Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n <namespace>

# Check resource constraints
kubectl describe nodes
kubectl top pods -n <namespace>

# Check image pull issues
kubectl get events --sort-by=.metadata.creationTimestamp -n <namespace>
```

#### Service Connectivity Issues

```bash
# Check service endpoints
kubectl get endpoints -n <namespace>

# Test service connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
# Inside pod: wget -qO- http://service-name:port/health
```

#### Database Connection Issues

```bash
# Check database pod logs
kubectl logs deployment/postgres -n <namespace>

# Test database connectivity
kubectl exec -it deployment/django-api -n <namespace> -- python manage.py dbshell
```

#### Performance Issues

```bash
# Check resource usage
kubectl top pods -n <namespace>

# Check HPA status
kubectl describe hpa -n <namespace>

# Check node resources
kubectl describe nodes
```

### Debug Commands

```bash
# Get cluster info
kubectl cluster-info

# Check all resources in namespace
kubectl get all -n <namespace>

# Describe problematic resources
kubectl describe deployment <deployment-name> -n <namespace>
kubectl describe service <service-name> -n <namespace>
kubectl describe ingress <ingress-name> -n <namespace>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp -n <namespace>
```

## 🔒 Security Considerations

### Network Security

```bash
# Apply network policies
kubectl apply -f infrastructure/k8s/base/network-policies.yaml

# Verify network policies
kubectl get networkpolicies -n <namespace>
```

### RBAC

```bash
# Apply RBAC configurations
kubectl apply -f infrastructure/k8s/base/rbac.yaml

# Check service account permissions
kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<service-account>
```

### Pod Security

```bash
# Check pod security contexts
kubectl get pods -o jsonpath='{.items[*].spec.securityContext}' -n <namespace>

# Verify non-root execution
kubectl exec <pod-name> -n <namespace> -- id
```

## 📈 Scaling Operations

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment prod-django-api --replicas=10 -n fullstack-monolith-prod

# Update HPA limits
kubectl patch hpa prod-django-api-hpa -p '{"spec":{"maxReplicas":20}}' -n fullstack-monolith-prod
```

### Cluster Scaling

```bash
# Add nodes (cloud provider specific)
# For GKE:
gcloud container clusters resize <cluster-name> --num-nodes=5 --zone=<zone>

# For EKS:
eksctl scale nodegroup --cluster=<cluster-name> --name=<nodegroup-name> --nodes=5
```

## 🔄 Maintenance Tasks

### Regular Maintenance

1. **Update base images monthly**
2. **Review and update resource requests/limits**
3. **Clean up old deployment revisions**
4. **Rotate secrets and certificates**
5. **Update Kubernetes cluster**

### Backup Procedures

```bash
# Backup persistent volumes
kubectl get pv -o yaml > pv-backup.yaml

# Backup application configuration
kubectl get configmaps,secrets -n <namespace> -o yaml > config-backup.yaml

# Backup deployment configurations
kubectl get deployments,services,ingresses -n <namespace> -o yaml > app-backup.yaml
```

### Disaster Recovery

```bash
# Restore from backup
kubectl apply -f pv-backup.yaml
kubectl apply -f config-backup.yaml
kubectl apply -f app-backup.yaml

# Verify restoration
kubectl get pods -n <namespace>
./infrastructure/k8s/scripts/test-deployment.ps1 -Environment <environment>
```

## 📞 Support and Escalation

### Support Channels

1. **Platform Team** - Cluster and infrastructure issues
2. **Development Team** - Application-specific issues
3. **Security Team** - Security-related concerns
4. **On-call Engineer** - Production emergencies

### Emergency Procedures

1. **Assess impact and severity**
2. **Check monitoring and alerts**
3. **Attempt quick fixes (restart, scale, rollback)**
4. **Escalate to appropriate team**
5. **Document incident and resolution**

### Contact Information

- **Platform Team**: platform-team@company.com
- **On-call**: +1-555-ON-CALL
- **Incident Management**: incidents@company.com
