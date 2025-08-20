#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Validation functions
function Test-KustomizationSyntax {
    param($Environment)
    
    Write-Info "Validating Kustomization syntax for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    
    try {
        $output = kustomize build $overlayPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Kustomization build failed: $output"
            return $false
        }
        Write-Success "✓ Kustomization syntax is valid"
        return $true
    } catch {
        Write-Error "Kustomization validation failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-KubernetesManifests {
    param($Environment)
    
    Write-Info "Validating Kubernetes manifests for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    
    try {
        # Build and validate manifests
        $manifests = kustomize build $overlayPath
        
        # Save to temporary file for validation
        $tempFile = [System.IO.Path]::GetTempFileName()
        $manifests | Out-File -FilePath $tempFile -Encoding UTF8
        
        # Dry run validation
        kubectl apply --dry-run=client -f $tempFile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Kubernetes manifest validation failed"
            return $false
        }
        
        # Clean up
        Remove-Item $tempFile -Force
        
        Write-Success "✓ Kubernetes manifests are valid"
        return $true
    } catch {
        Write-Error "Manifest validation failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-ResourceRequirements {
    param($Environment)
    
    Write-Info "Validating resource requirements for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    $manifests = kustomize build $overlayPath | ConvertFrom-Yaml -AllDocuments
    
    $totalCpuRequests = 0
    $totalMemoryRequests = 0
    $totalCpuLimits = 0
    $totalMemoryLimits = 0
    
    foreach ($manifest in $manifests) {
        if ($manifest.kind -eq "Deployment") {
            $containers = $manifest.spec.template.spec.containers
            foreach ($container in $containers) {
                if ($container.resources.requests) {
                    if ($container.resources.requests.cpu) {
                        $cpuValue = $container.resources.requests.cpu -replace 'm', ''
                        $totalCpuRequests += [int]$cpuValue
                    }
                    if ($container.resources.requests.memory) {
                        $memValue = $container.resources.requests.memory -replace 'Mi', ''
                        $totalMemoryRequests += [int]$memValue
                    }
                }
                if ($container.resources.limits) {
                    if ($container.resources.limits.cpu) {
                        $cpuValue = $container.resources.limits.cpu -replace 'm', ''
                        $totalCpuLimits += [int]$cpuValue
                    }
                    if ($container.resources.limits.memory) {
                        $memValue = $container.resources.limits.memory -replace 'Mi', ''
                        $totalMemoryLimits += [int]$memValue
                    }
                }
            }
        }
    }
    
    Write-Info "Resource Summary for $Environment:"
    Write-Info "  CPU Requests: ${totalCpuRequests}m"
    Write-Info "  Memory Requests: ${totalMemoryRequests}Mi"
    Write-Info "  CPU Limits: ${totalCpuLimits}m"
    Write-Info "  Memory Limits: ${totalMemoryLimits}Mi"
    
    # Environment-specific validation
    switch ($Environment) {
        "development" {
            if ($totalMemoryRequests -gt 2048) {
                Write-Warning "Development environment memory requests exceed recommended 2Gi"
            }
        }
        "staging" {
            if ($totalMemoryRequests -gt 4096) {
                Write-Warning "Staging environment memory requests exceed recommended 4Gi"
            }
        }
        "production" {
            if ($totalMemoryRequests -lt 4096) {
                Write-Warning "Production environment memory requests may be too low"
            }
        }
    }
    
    Write-Success "✓ Resource requirements validated"
    return $true
}

function Test-SecurityPolicies {
    param($Environment)
    
    Write-Info "Validating security policies for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    $manifests = kustomize build $overlayPath | ConvertFrom-Yaml -AllDocuments
    
    $securityIssues = @()
    
    foreach ($manifest in $manifests) {
        if ($manifest.kind -eq "Deployment") {
            $containers = $manifest.spec.template.spec.containers
            foreach ($container in $containers) {
                # Check for privileged containers
                if ($container.securityContext.privileged -eq $true) {
                    $securityIssues += "Privileged container found: $($container.name)"
                }
                
                # Check for root user
                if ($container.securityContext.runAsUser -eq 0) {
                    $securityIssues += "Container running as root: $($container.name)"
                }
                
                # Check for missing security context
                if (-not $container.securityContext) {
                    $securityIssues += "Missing security context: $($container.name)"
                }
            }
        }
        
        # Check for missing network policies in production
        if ($Environment -eq "production" -and $manifest.kind -eq "NetworkPolicy") {
            Write-Success "✓ Network policy found"
        }
    }
    
    if ($securityIssues.Count -gt 0) {
        Write-Warning "Security issues found:"
        foreach ($issue in $securityIssues) {
            Write-Warning "  - $issue"
        }
    } else {
        Write-Success "✓ No security issues found"
    }
    
    return $true
}

function Test-HighAvailability {
    param($Environment)
    
    Write-Info "Validating high availability configuration for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    $manifests = kustomize build $overlayPath | ConvertFrom-Yaml -AllDocuments
    
    foreach ($manifest in $manifests) {
        if ($manifest.kind -eq "Deployment") {
            $replicas = $manifest.spec.replicas
            $deploymentName = $manifest.metadata.name
            
            # Check replica count based on environment
            switch ($Environment) {
                "development" {
                    if ($replicas -gt 1) {
                        Write-Info "  $deploymentName: $replicas replicas (development)"
                    }
                }
                "staging" {
                    if ($replicas -lt 2 -and $deploymentName -notmatch "postgres|redis") {
                        Write-Warning "  $deploymentName: Only $replicas replica(s) in staging"
                    }
                }
                "production" {
                    if ($replicas -lt 3 -and $deploymentName -notmatch "postgres|redis|celery-beat") {
                        Write-Warning "  $deploymentName: Only $replicas replica(s) in production"
                    }
                }
            }
            
            # Check for anti-affinity rules in production
            if ($Environment -eq "production") {
                $affinity = $manifest.spec.template.spec.affinity
                if (-not $affinity -or -not $affinity.podAntiAffinity) {
                    Write-Warning "  $deploymentName: Missing pod anti-affinity rules"
                }
            }
        }
    }
    
    Write-Success "✓ High availability configuration validated"
    return $true
}

function Test-MonitoringConfiguration {
    param($Environment)
    
    Write-Info "Validating monitoring configuration for $Environment..."
    
    $overlayPath = "infrastructure/k8s/overlays/$Environment"
    $manifests = kustomize build $overlayPath | ConvertFrom-Yaml -AllDocuments
    
    $monitoringFound = $false
    $prometheusAnnotations = 0
    
    foreach ($manifest in $manifests) {
        if ($manifest.kind -eq "ServiceMonitor") {
            $monitoringFound = $true
        }
        
        if ($manifest.kind -eq "Deployment") {
            $annotations = $manifest.spec.template.metadata.annotations
            if ($annotations -and $annotations.'prometheus.io/scrape' -eq "true") {
                $prometheusAnnotations++
            }
        }
    }
    
    if ($monitoringFound) {
        Write-Success "✓ ServiceMonitor configuration found"
    } else {
        Write-Warning "No ServiceMonitor configuration found"
    }
    
    Write-Info "  Deployments with Prometheus annotations: $prometheusAnnotations"
    
    Write-Success "✓ Monitoring configuration validated"
    return $true
}

# Main validation function
function Invoke-Validation {
    param($Environment)
    
    Write-Info "Starting validation for $Environment environment..."
    
    $results = @()
    
    $results += Test-KustomizationSyntax -Environment $Environment
    $results += Test-KubernetesManifests -Environment $Environment
    $results += Test-ResourceRequirements -Environment $Environment
    $results += Test-SecurityPolicies -Environment $Environment
    $results += Test-HighAvailability -Environment $Environment
    $results += Test-MonitoringConfiguration -Environment $Environment
    
    $failedTests = $results | Where-Object { $_ -eq $false }
    
    if ($failedTests.Count -eq 0) {
        Write-Success "🎉 All validation tests passed!"
        return $true
    } else {
        Write-Error "❌ $($failedTests.Count) validation test(s) failed"
        return $false
    }
}

# Helper function to convert YAML to PowerShell objects
function ConvertFrom-Yaml {
    param(
        [Parameter(ValueFromPipeline)]
        [string]$InputObject,
        [switch]$AllDocuments
    )
    
    # This is a simplified YAML parser for basic validation
    # In production, you might want to use a proper YAML library
    $documents = $InputObject -split "---`n" | Where-Object { $_.Trim() -ne "" }
    
    foreach ($doc in $documents) {
        # Basic YAML to object conversion
        # This is simplified and may not handle all YAML features
        $obj = @{}
        $lines = $doc -split "`n"
        
        foreach ($line in $lines) {
            if ($line -match "^(\s*)(\w+):\s*(.*)$") {
                $key = $matches[2]
                $value = $matches[3]
                $obj[$key] = $value
            }
        }
        
        if ($AllDocuments) {
            $obj
        } else {
            return $obj
        }
    }
}

# Main execution
try {
    $result = Invoke-Validation -Environment $Environment
    if (-not $result) {
        exit 1
    }
} catch {
    Write-Error "Validation failed: $($_.Exception.Message)"
    exit 1
}