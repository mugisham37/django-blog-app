#!/bin/bash

set -euo pipefail

# Default values
ENVIRONMENT=""
IMAGE_TAG="latest"
DRY_RUN=false
ROLLBACK=false
ROLLBACK_REVISION=""
WAIT_FOR_READY=true
TIMEOUT=600

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Usage function
usage() {
    cat << EOF
Usage: $0 -e ENVIRONMENT [OPTIONS]

Deploy fullstack monolith to Kubernetes

Required:
    -e, --environment    Target environment (development|staging|production)

Options:
    -t, --tag           Image tag to deploy (default: latest)
    -d, --dry-run       Perform dry run without applying changes
    -r, --rollback      Rollback to previous deployment
    --rollback-revision Specific revision to rollback to
    --no-wait          Don't wait for deployment to be ready
    --timeout          Timeout in seconds for waiting (default: 600)
    -h, --help         Show this help message

Examples:
    $0 -e development
    $0 -e production -t v1.2.3
    $0 -e staging --dry-run
    $0 -e production --rollback
    $0 -e production --rollback --rollback-revision 5
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        --rollback-revision)
            ROLLBACK_REVISION="$2"
            shift 2
            ;;
        --no-wait)
            WAIT_FOR_READY=false
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    usage
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Environment must be one of: development, staging, production"
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    log_success "✓ kubectl is available"
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_error "kustomize is not installed or not in PATH"
        exit 1
    fi
    log_success "✓ kustomize is available"
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    log_success "✓ Kubernetes cluster is accessible"
}

# Deploy application
deploy_application() {
    local env="$1"
    local tag="$2"
    local dry_run="$3"
    
    log_info "Starting deployment to $env environment..."
    
    local overlay_path="infrastructure/k8s/overlays/$env"
    
    if [[ ! -d "$overlay_path" ]]; then
        log_error "Overlay path $overlay_path does not exist"
        exit 1
    fi
    
    # Build kustomization
    log_info "Building Kubernetes manifests..."
    local manifests
    if ! manifests=$(kustomize build "$overlay_path"); then
        log_error "Failed to build kustomization"
        exit 1
    fi
    
    # Update image tags if specified
    if [[ "$tag" != "latest" ]]; then
        log_info "Updating image tags to $tag..."
        manifests=$(echo "$manifests" | sed -e "s/django-api:latest/django-api:$tag/g" -e "s/nextjs-web:latest/nextjs-web:$tag/g")
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be applied"
        log_info "Generated manifests:"
        echo "$manifests"
        return
    fi
    
    # Apply manifests
    log_info "Applying Kubernetes manifests..."
    if ! echo "$manifests" | kubectl apply -f -; then
        log_error "Failed to apply manifests"
        exit 1
    fi
    
    log_success "✓ Manifests applied successfully"
}

# Rollback deployment
rollback_deployment() {
    local env="$1"
    local revision="$2"
    
    log_warning "Rolling back deployment in $env environment..."
    
    local namespace="fullstack-monolith-$env"
    if [[ "$env" == "production" ]]; then
        namespace="fullstack-monolith-prod"
    fi
    
    local deployments=("django-api" "nextjs-web" "nginx-proxy" "django-celery-worker")
    
    for deployment in "${deployments[@]}"; do
        local deployment_name="$env-$deployment"
        if [[ "$env" == "production" ]]; then
            deployment_name="prod-$deployment"
        fi
        
        log_info "Rolling back $deployment_name..."
        
        if [[ -n "$revision" ]]; then
            if ! kubectl rollout undo "deployment/$deployment_name" --namespace="$namespace" --to-revision="$revision"; then
                log_error "Failed to rollback $deployment_name"
                exit 1
            fi
        else
            if ! kubectl rollout undo "deployment/$deployment_name" --namespace="$namespace"; then
                log_error "Failed to rollback $deployment_name"
                exit 1
            fi
        fi
    done
    
    log_success "✓ Rollback completed"
}

# Wait for deployment to be ready
wait_for_deployment() {
    local env="$1"
    local timeout="$2"
    
    log_info "Waiting for deployment to be ready (timeout: ${timeout}s)..."
    
    local namespace="fullstack-monolith-$env"
    if [[ "$env" == "production" ]]; then
        namespace="fullstack-monolith-prod"
    fi
    
    local deployments=("django-api" "nextjs-web" "nginx-proxy" "django-celery-worker")
    
    for deployment in "${deployments[@]}"; do
        local deployment_name="$env-$deployment"
        if [[ "$env" == "production" ]]; then
            deployment_name="prod-$deployment"
        fi
        
        log_info "Waiting for $deployment_name to be ready..."
        
        if ! kubectl rollout status "deployment/$deployment_name" --namespace="$namespace" --timeout="${timeout}s"; then
            log_error "Deployment $deployment_name failed to become ready within timeout"
            exit 1
        fi
    done
    
    log_success "✓ All deployments are ready"
}

# Health check
check_deployment_health() {
    local env="$1"
    
    log_info "Performing health checks..."
    
    local namespace="fullstack-monolith-$env"
    if [[ "$env" == "production" ]]; then
        namespace="fullstack-monolith-prod"
    fi
    
    # Check pod status
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods --namespace="$namespace" --output=json | jq -r '.items[] | select(.status.phase != "Running" or (.status.containerStatuses[]?.ready == false)) | .metadata.name' 2>/dev/null || true)
    
    if [[ -n "$unhealthy_pods" ]]; then
        log_warning "Found unhealthy pods:"
        echo "$unhealthy_pods" | while read -r pod; do
            log_warning "  - $pod"
        done
    else
        log_success "✓ All pods are healthy"
    fi
    
    # Check service endpoints
    log_info "Checking service endpoints..."
    kubectl get endpoints --namespace="$namespace"
    
    log_success "✓ Health check completed"
}

# Main execution
main() {
    log_info "Kubernetes Deployment Script"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "Dry Run: $DRY_RUN"
    log_info "Rollback: $ROLLBACK"
    
    check_prerequisites
    
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment "$ENVIRONMENT" "$ROLLBACK_REVISION"
    else
        deploy_application "$ENVIRONMENT" "$IMAGE_TAG" "$DRY_RUN"
    fi
    
    if [[ "$DRY_RUN" != "true" && "$WAIT_FOR_READY" == "true" ]]; then
        wait_for_deployment "$ENVIRONMENT" "$TIMEOUT"
        check_deployment_health "$ENVIRONMENT"
    fi
    
    log_success "🎉 Deployment completed successfully!"
}

# Trap errors
trap 'log_error "Deployment failed on line $LINENO"' ERR

# Run main function
main "$@"