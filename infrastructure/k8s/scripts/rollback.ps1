#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$Revision = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Component = "all",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false,
    
    [Parameter(Mandatory=$false)]
    [int]$Timeout = 600
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Get namespace for environment
function Get-Namespace {
    param($Environment)
    
    switch ($Environment) {
        "development" { return "fullstack-monolith-dev" }
        "staging" { return "fullstack-monolith-staging" }
        "production" { return "fullstack-monolith-prod" }
        default { return "fullstack-monolith-$Environment" }
    }
}

# Get deployment name with prefix
function Get-DeploymentName {
    param($Environment, $Component)
    
    $prefix = switch ($Environment) {
        "development" { "dev-" }
        "staging" { "staging-" }
        "production" { "prod-" }
        default { "$Environment-" }
    }
    
    return "$prefix$Component"
}

# List available revisions
function Get-DeploymentRevisions {
    param($Environment, $Component)
    
    $namespace = Get-Namespace -Environment $Environment
    $deploymentName = Get-DeploymentName -Environment $Environment -Component $Component
    
    Write-Info "Available revisions for $deploymentName in $namespace:"
    
    try {
        $revisions = kubectl rollout history "deployment/$deploymentName" --namespace=$namespace
        Write-Host $revisions
        
        # Parse revision numbers
        $revisionNumbers = @()
        $lines = $revisions -split "`n"
        foreach ($line in $lines) {
            if ($line -match "^\s*(\d+)\s+") {
                $revisionNumbers += [int]$matches[1]
            }
        }
        
        return $revisionNumbers
    } catch {
        Write-Error "Failed to get revision history for $deploymentName: $($_.Exception.Message)"
        return @()
    }
}

# Get current deployment status
function Get-DeploymentStatus {
    param($Environment, $Component)
    
    $namespace = Get-Namespace -Environment $Environment
    $deploymentName = Get-DeploymentName -Environment $Environment -Component $Component
    
    try {
        $deployment = kubectl get deployment $deploymentName --namespace=$namespace --output=json | ConvertFrom-Json
        
        $status = @{
            Name = $deploymentName
            Replicas = $deployment.spec.replicas
            ReadyReplicas = $deployment.status.readyReplicas
            UpdatedReplicas = $deployment.status.updatedReplicas
            AvailableReplicas = $deployment.status.availableReplicas
            Generation = $deployment.metadata.generation
            ObservedGeneration = $deployment.status.observedGeneration
        }
        
        return $status
    } catch {
        Write-Error "Failed to get deployment status for $deploymentName: $($_.Exception.Message)"
        return $null
    }
}

# Perform rollback
function Invoke-Rollback {
    param($Environment, $Component, $Revision, $DryRun)
    
    $namespace = Get-Namespace -Environment $Environment
    $deploymentName = Get-DeploymentName -Environment $Environment -Component $Component
    
    Write-Info "Rolling back $deploymentName in $namespace..."
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No actual rollback will be performed"
        
        if ($Revision) {
            Write-Info "Would rollback to revision: $Revision"
        } else {
            Write-Info "Would rollback to previous revision"
        }
        return $true
    }
    
    # Get current status before rollback
    $currentStatus = Get-DeploymentStatus -Environment $Environment -Component $Component
    if ($currentStatus) {
        Write-Info "Current status: $($currentStatus.ReadyReplicas)/$($currentStatus.Replicas) replicas ready"
    }
    
    try {
        if ($Revision) {
            Write-Info "Rolling back to revision $Revision..."
            kubectl rollout undo "deployment/$deploymentName" --namespace=$namespace --to-revision=$Revision
        } else {
            Write-Info "Rolling back to previous revision..."
            kubectl rollout undo "deployment/$deploymentName" --namespace=$namespace
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Rollback command failed"
            return $false
        }
        
        Write-Success "✓ Rollback initiated for $deploymentName"
        return $true
        
    } catch {
        Write-Error "Failed to rollback $deploymentName: $($_.Exception.Message)"
        return $false
    }
}

# Wait for rollback to complete
function Wait-ForRollback {
    param($Environment, $Component, $Timeout)
    
    $namespace = Get-Namespace -Environment $Environment
    $deploymentName = Get-DeploymentName -Environment $Environment -Component $Component
    
    Write-Info "Waiting for rollback to complete (timeout: ${Timeout}s)..."
    
    try {
        kubectl rollout status "deployment/$deploymentName" --namespace=$namespace --timeout="${Timeout}s"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Rollback completed successfully for $deploymentName"
            return $true
        } else {
            Write-Error "Rollback failed or timed out for $deploymentName"
            return $false
        }
    } catch {
        Write-Error "Failed to wait for rollback completion: $($_.Exception.Message)"
        return $false
    }
}

# Verify rollback success
function Test-RollbackSuccess {
    param($Environment, $Component)
    
    Write-Info "Verifying rollback success for $Component..."
    
    $status = Get-DeploymentStatus -Environment $Environment -Component $Component
    
    if (-not $status) {
        Write-Error "Could not get deployment status"
        return $false
    }
    
    if ($status.ReadyReplicas -eq $status.Replicas -and $status.ReadyReplicas -gt 0) {
        Write-Success "✓ All replicas are ready: $($status.ReadyReplicas)/$($status.Replicas)"
        return $true
    } else {
        Write-Warning "⚠ Not all replicas are ready: $($status.ReadyReplicas)/$($status.Replicas)"
        return $false
    }
}

# Rollback all components
function Invoke-FullRollback {
    param($Environment, $Revision, $DryRun)
    
    $components = @("django-api", "nextjs-web", "nginx-proxy", "django-celery-worker")
    $results = @()
    
    Write-Info "Performing full rollback for all components..."
    
    foreach ($component in $components) {
        Write-Info "Processing component: $component"
        
        # Check if deployment exists
        $namespace = Get-Namespace -Environment $Environment
        $deploymentName = Get-DeploymentName -Environment $Environment -Component $component
        
        try {
            kubectl get deployment $deploymentName --namespace=$namespace | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                $result = Invoke-Rollback -Environment $Environment -Component $component -Revision $Revision -DryRun $DryRun
                $results += $result
                
                if ($result -and -not $DryRun) {
                    $waitResult = Wait-ForRollback -Environment $Environment -Component $component -Timeout $Timeout
                    $results += $waitResult
                    
                    if ($waitResult) {
                        $verifyResult = Test-RollbackSuccess -Environment $Environment -Component $component
                        $results += $verifyResult
                    }
                }
            } else {
                Write-Warning "Deployment $deploymentName not found, skipping..."
            }
        } catch {
            Write-Warning "Failed to check deployment $deploymentName, skipping..."
        }
    }
    
    $failedResults = $results | Where-Object { $_ -eq $false }
    
    if ($failedResults.Count -eq 0) {
        Write-Success "🎉 Full rollback completed successfully!"
        return $true
    } else {
        Write-Error "❌ $($failedResults.Count) rollback operation(s) failed"
        return $false
    }
}

# Interactive rollback selection
function Invoke-InteractiveRollback {
    param($Environment, $Component)
    
    Write-Info "Interactive rollback for $Component in $Environment environment"
    
    # Get available revisions
    $revisions = Get-DeploymentRevisions -Environment $Environment -Component $Component
    
    if ($revisions.Count -eq 0) {
        Write-Error "No revisions available for rollback"
        return $false
    }
    
    # Show current status
    $currentStatus = Get-DeploymentStatus -Environment $Environment -Component $Component
    if ($currentStatus) {
        Write-Info "Current deployment status:"
        Write-Info "  Replicas: $($currentStatus.ReadyReplicas)/$($currentStatus.Replicas)"
        Write-Info "  Generation: $($currentStatus.Generation)"
    }
    
    # Prompt for revision selection
    Write-Info "Available revisions: $($revisions -join ', ')"
    $selectedRevision = Read-Host "Enter revision number to rollback to (or press Enter for previous revision)"
    
    if ($selectedRevision -and $selectedRevision -notin $revisions) {
        Write-Error "Invalid revision number: $selectedRevision"
        return $false
    }
    
    # Confirm rollback
    $confirmMessage = if ($selectedRevision) {
        "rollback to revision $selectedRevision"
    } else {
        "rollback to previous revision"
    }
    
    $confirmation = Read-Host "Are you sure you want to $confirmMessage for $Component? (y/N)"
    
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-Info "Rollback cancelled by user"
        return $false
    }
    
    # Perform rollback
    $result = Invoke-Rollback -Environment $Environment -Component $Component -Revision $selectedRevision -DryRun $false
    
    if ($result) {
        $waitResult = Wait-ForRollback -Environment $Environment -Component $Component -Timeout $Timeout
        if ($waitResult) {
            Test-RollbackSuccess -Environment $Environment -Component $Component
        }
    }
    
    return $result
}

# Main execution
function Main {
    Write-Info "Kubernetes Rollback Script"
    Write-Info "Environment: $Environment"
    Write-Info "Component: $Component"
    Write-Info "Revision: $(if ($Revision) { $Revision } else { 'Previous' })"
    Write-Info "Dry Run: $DryRun"
    
    # Production safety check
    if ($Environment -eq "production" -and -not $Force -and -not $DryRun) {
        Write-Warning "⚠ PRODUCTION ROLLBACK WARNING ⚠"
        Write-Warning "You are about to rollback in the production environment."
        Write-Warning "This operation can affect live users and services."
        
        $confirmation = Read-Host "Are you absolutely sure you want to proceed? Type 'ROLLBACK' to confirm"
        
        if ($confirmation -ne "ROLLBACK") {
            Write-Info "Production rollback cancelled for safety"
            Write-Info "Use --Force flag to bypass this check if needed"
            exit 0
        }
    }
    
    try {
        if ($Component -eq "all") {
            $result = Invoke-FullRollback -Environment $Environment -Revision $Revision -DryRun $DryRun
        } elseif ($Component -eq "interactive") {
            Write-Info "Starting interactive rollback mode..."
            $components = @("django-api", "nextjs-web", "nginx-proxy", "django-celery-worker")
            
            Write-Info "Available components:"
            for ($i = 0; $i -lt $components.Count; $i++) {
                Write-Info "  $($i + 1). $($components[$i])"
            }
            
            $selection = Read-Host "Select component number (1-$($components.Count))"
            
            try {
                $selectedIndex = [int]$selection - 1
                if ($selectedIndex -ge 0 -and $selectedIndex -lt $components.Count) {
                    $selectedComponent = $components[$selectedIndex]
                    $result = Invoke-InteractiveRollback -Environment $Environment -Component $selectedComponent
                } else {
                    Write-Error "Invalid selection: $selection"
                    exit 1
                }
            } catch {
                Write-Error "Invalid selection: $selection"
                exit 1
            }
        } else {
            $result = Invoke-Rollback -Environment $Environment -Component $Component -Revision $Revision -DryRun $DryRun
            
            if ($result -and -not $DryRun) {
                $waitResult = Wait-ForRollback -Environment $Environment -Component $Component -Timeout $Timeout
                if ($waitResult) {
                    $result = Test-RollbackSuccess -Environment $Environment -Component $Component
                }
            }
        }
        
        if (-not $result) {
            exit 1
        }
        
    } catch {
        Write-Error "Rollback failed: $($_.Exception.Message)"
        exit 1
    }
}

# Execute main function
Main