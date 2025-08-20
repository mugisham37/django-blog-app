#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Rollback = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$RollbackRevision = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$WaitForReady = $true,
    
    [Parameter(Mandatory=$false)]
    [int]$Timeout = 600
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Validate prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check kubectl
    try {
        kubectl version --client --output=json | Out-Null
        Write-Success "✓ kubectl is available"
    } catch {
        Write-Error "✗ kubectl is not available or not configured"
        exit 1
    }
    
    # Check kustomize
    try {
        kustomize version | Out-Null
        Write-Success "✓ kustomize is available"
    } catch {
        Write-Error "✗ kustomize is not available"
        exit 1
    }
    
    # Check cluster connectivity
    try {
        kubectl cluster-info | Out-Null
        Write-Success "✓ Kubernetes cluster is accessible"
    } catch {
        Write-Error "✗ Cannot connect to Kubernetes cluster"
        exit 1
    }
}

# Deploy function
function Deploy-Application {
    param($Environment, $ImageTag, $DryRun)
    
    Write-Info "Starting deployment to $Environment environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    
    if (-not (Test-Path $overlayPath)) {
        Write-Error "Overlay path $overlayPath does not exist"
        exit 1
    }
    
    # Build kustomization
    Write-Info "Building Kubernetes manifests..."
    $manifests = kustomize build $overlayPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build kustomization"
        exit 1
    }
    
    # Update image tags if specified
    if ($ImageTag -ne "latest") {
        Write-Info "Updating image tags to $ImageTag..."
        $manifests = $manifests | ForEach-Object {
            $_ -replace "django-api:latest", "django-api:$ImageTag" -replace "nextjs-web:latest", "nextjs-web:$ImageTag"
        }
    }
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No changes will be applied"
        Write-Info "Generated manifests:"
        $manifests
        return
    }
    
    # Apply manifests
    Write-Info "Applying Kubernetes manifests..."
    $manifests | kubectl apply -f -
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply manifests"
        exit 1
    }
    
    Write-Success "✓ Manifests applied successfully"
}

# Rollback function
function Rollback-Deployment {
    param($Environment, $Revision)
    
    Write-Warning "Rolling back deployment in $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    $deployments = @("django-api", "nextjs-web", "nginx-proxy", "django-celery-worker")
    
    foreach ($deployment in $deployments) {
        $deploymentName = "$Environment-$deployment"
        if ($Environment -eq "production") { $deploymentName = "prod-$deployment" }
        
        Write-Info "Rolling back $deploymentName..."
        
        if ($Revision) {
            kubectl rollout undo deployment/$deploymentName --namespace=$namespace --to-revision=$Revision
        } else {
            kubectl rollout undo deployment/$deploymentName --namespace=$namespace
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to rollback $deploymentName"
            exit 1
        }
    }
    
    Write-Success "✓ Rollback completed"
}

# Wait for deployment to be ready
function Wait-ForDeployment {
    param($Environment, $Timeout)
    
    Write-Info "Waiting for deployment to be ready (timeout: ${Timeout}s)..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    $deployments = @("django-api", "nextjs-web", "nginx-proxy", "django-celery-worker")
    
    foreach ($deployment in $deployments) {
        $deploymentName = "$Environment-$deployment"
        if ($Environment -eq "production") { $deploymentName = "prod-$deployment" }
        
        Write-Info "Waiting for $deploymentName to be ready..."
        
        kubectl rollout status deployment/$deploymentName --namespace=$namespace --timeout="${Timeout}s"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Deployment $deploymentName failed to become ready within timeout"
            exit 1
        }
    }
    
    Write-Success "✓ All deployments are ready"
}

# Health check function
function Test-DeploymentHealth {
    param($Environment)
    
    Write-Info "Performing health checks..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    # Check pod status
    $pods = kubectl get pods --namespace=$namespace --output=json | ConvertFrom-Json
    
    $unhealthyPods = $pods.items | Where-Object { 
        $_.status.phase -ne "Running" -or 
        ($_.status.containerStatuses | Where-Object { $_.ready -eq $false }).Count -gt 0 
    }
    
    if ($unhealthyPods.Count -gt 0) {
        Write-Warning "Found unhealthy pods:"
        $unhealthyPods | ForEach-Object { Write-Warning "  - $($_.metadata.name): $($_.status.phase)" }
    } else {
        Write-Success "✓ All pods are healthy"
    }
    
    # Check service endpoints
    Write-Info "Checking service endpoints..."
    kubectl get endpoints --namespace=$namespace
    
    Write-Success "✓ Health check completed"
}

# Main execution
try {
    Write-Info "Kubernetes Deployment Script"
    Write-Info "Environment: $Environment"
    Write-Info "Image Tag: $ImageTag"
    Write-Info "Dry Run: $DryRun"
    Write-Info "Rollback: $Rollback"
    
    Test-Prerequisites
    
    if ($Rollback) {
        Rollback-Deployment -Environment $Environment -Revision $RollbackRevision
    } else {
        Deploy-Application -Environment $Environment -ImageTag $ImageTag -DryRun $DryRun
    }
    
    if (-not $DryRun -and $WaitForReady) {
        Wait-ForDeployment -Environment $Environment -Timeout $Timeout
        Test-DeploymentHealth -Environment $Environment
    }
    
    Write-Success "🎉 Deployment completed successfully!"
    
} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}