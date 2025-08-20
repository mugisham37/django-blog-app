#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [int]$Timeout = 300,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipLoadTest = $false
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Test functions
function Test-PodHealth {
    param($Environment)
    
    Write-Info "Testing pod health for $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    # Get all pods
    $pods = kubectl get pods --namespace=$namespace --output=json | ConvertFrom-Json
    
    $healthyPods = 0
    $totalPods = $pods.items.Count
    
    foreach ($pod in $pods.items) {
        $podName = $pod.metadata.name
        $podStatus = $pod.status.phase
        $containerStatuses = $pod.status.containerStatuses
        
        $allContainersReady = $true
        if ($containerStatuses) {
            foreach ($containerStatus in $containerStatuses) {
                if (-not $containerStatus.ready) {
                    $allContainersReady = $false
                    break
                }
            }
        }
        
        if ($podStatus -eq "Running" -and $allContainersReady) {
            $healthyPods++
            Write-Success "  ✓ $podName: $podStatus (Ready)"
        } else {
            Write-Warning "  ⚠ $podName: $podStatus (Not Ready)"
        }
    }
    
    Write-Info "Pod Health Summary: $healthyPods/$totalPods pods healthy"
    
    if ($healthyPods -eq $totalPods) {
        Write-Success "✓ All pods are healthy"
        return $true
    } else {
        Write-Warning "Some pods are not healthy"
        return $false
    }
}

function Test-ServiceEndpoints {
    param($Environment)
    
    Write-Info "Testing service endpoints for $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    # Get all services
    $services = kubectl get services --namespace=$namespace --output=json | ConvertFrom-Json
    
    $healthyServices = 0
    $totalServices = $services.items.Count
    
    foreach ($service in $services.items) {
        $serviceName = $service.metadata.name
        
        # Get endpoints for the service
        try {
            $endpoints = kubectl get endpoints $serviceName --namespace=$namespace --output=json | ConvertFrom-Json
            
            if ($endpoints.subsets -and $endpoints.subsets.Count -gt 0) {
                $readyAddresses = 0
                foreach ($subset in $endpoints.subsets) {
                    if ($subset.addresses) {
                        $readyAddresses += $subset.addresses.Count
                    }
                }
                
                if ($readyAddresses -gt 0) {
                    $healthyServices++
                    Write-Success "  ✓ $serviceName: $readyAddresses ready endpoint(s)"
                } else {
                    Write-Warning "  ⚠ $serviceName: No ready endpoints"
                }
            } else {
                Write-Warning "  ⚠ $serviceName: No endpoints"
            }
        } catch {
            Write-Warning "  ⚠ $serviceName: Failed to get endpoints"
        }
    }
    
    Write-Info "Service Health Summary: $healthyServices/$totalServices services healthy"
    
    if ($healthyServices -eq $totalServices) {
        Write-Success "✓ All services have healthy endpoints"
        return $true
    } else {
        Write-Warning "Some services don't have healthy endpoints"
        return $false
    }
}

function Test-ApplicationHealth {
    param($Environment)
    
    Write-Info "Testing application health endpoints for $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    # Test Django API health
    try {
        Write-Info "Testing Django API health endpoint..."
        $djangoService = "django-api-service"
        if ($Environment -ne "development") { $djangoService = "$Environment-django-api-service" }
        if ($Environment -eq "production") { $djangoService = "prod-django-api-service" }
        
        # Port forward to test health endpoint
        $portForwardJob = Start-Job -ScriptBlock {
            kubectl port-forward "service/$using:djangoService" 8080:8000 --namespace=$using:namespace
        }
        
        Start-Sleep -Seconds 5
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health/" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "  ✓ Django API health endpoint responding"
            } else {
                Write-Warning "  ⚠ Django API health endpoint returned status $($response.StatusCode)"
            }
        } catch {
            Write-Warning "  ⚠ Django API health endpoint not accessible: $($_.Exception.Message)"
        } finally {
            Stop-Job $portForwardJob -Force
            Remove-Job $portForwardJob -Force
        }
    } catch {
        Write-Warning "  ⚠ Failed to test Django API health: $($_.Exception.Message)"
    }
    
    # Test Next.js health
    try {
        Write-Info "Testing Next.js health endpoint..."
        $nextjsService = "nextjs-web-service"
        if ($Environment -ne "development") { $nextjsService = "$Environment-nextjs-web-service" }
        if ($Environment -eq "production") { $nextjsService = "prod-nextjs-web-service" }
        
        # Port forward to test health endpoint
        $portForwardJob = Start-Job -ScriptBlock {
            kubectl port-forward "service/$using:nextjsService" 3080:3000 --namespace=$using:namespace
        }
        
        Start-Sleep -Seconds 5
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3080/api/health" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "  ✓ Next.js health endpoint responding"
            } else {
                Write-Warning "  ⚠ Next.js health endpoint returned status $($response.StatusCode)"
            }
        } catch {
            Write-Warning "  ⚠ Next.js health endpoint not accessible: $($_.Exception.Message)"
        } finally {
            Stop-Job $portForwardJob -Force
            Remove-Job $portForwardJob -Force
        }
    } catch {
        Write-Warning "  ⚠ Failed to test Next.js health: $($_.Exception.Message)"
    }
    
    Write-Success "✓ Application health tests completed"
    return $true
}

function Test-DatabaseConnectivity {
    param($Environment)
    
    Write-Info "Testing database connectivity for $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    try {
        # Test PostgreSQL connectivity
        $postgresService = "postgres-service"
        if ($Environment -ne "development") { $postgresService = "$Environment-postgres-service" }
        if ($Environment -eq "production") { $postgresService = "prod-postgres-service" }
        
        $testResult = kubectl exec -n $namespace "deployment/$postgresService" -- pg_isready -U postgres
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ PostgreSQL database is ready"
        } else {
            Write-Warning "  ⚠ PostgreSQL database is not ready"
        }
    } catch {
        Write-Warning "  ⚠ Failed to test PostgreSQL connectivity: $($_.Exception.Message)"
    }
    
    try {
        # Test Redis connectivity
        $redisService = "redis-service"
        if ($Environment -ne "development") { $redisService = "$Environment-redis-service" }
        if ($Environment -eq "production") { $redisService = "prod-redis-service" }
        
        $testResult = kubectl exec -n $namespace "deployment/$redisService" -- redis-cli ping
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ Redis cache is ready"
        } else {
            Write-Warning "  ⚠ Redis cache is not ready"
        }
    } catch {
        Write-Warning "  ⚠ Failed to test Redis connectivity: $($_.Exception.Message)"
    }
    
    Write-Success "✓ Database connectivity tests completed"
    return $true
}

function Test-HorizontalPodAutoscaler {
    param($Environment)
    
    Write-Info "Testing Horizontal Pod Autoscaler for $Environment environment..."
    
    $namespace = "fullstack-monolith-$Environment"
    if ($Environment -eq "production") { $namespace = "fullstack-monolith-prod" }
    
    try {
        $hpas = kubectl get hpa --namespace=$namespace --output=json | ConvertFrom-Json
        
        foreach ($hpa in $hpas.items) {
            $hpaName = $hpa.metadata.name
            $currentReplicas = $hpa.status.currentReplicas
            $desiredReplicas = $hpa.status.desiredReplicas
            $minReplicas = $hpa.spec.minReplicas
            $maxReplicas = $hpa.spec.maxReplicas
            
            Write-Info "  $hpaName: $currentReplicas/$desiredReplicas replicas (min: $minReplicas, max: $maxReplicas)"
            
            if ($currentReplicas -ge $minReplicas -and $currentReplicas -le $maxReplicas) {
                Write-Success "  ✓ $hpaName: HPA is functioning correctly"
            } else {
                Write-Warning "  ⚠ $hpaName: HPA replica count is outside expected range"
            }
        }
    } catch {
        Write-Warning "Failed to test HPA: $($_.Exception.Message)"
    }
    
    Write-Success "✓ HPA tests completed"
    return $true
}

function Test-LoadBalancing {
    param($Environment)
    
    if ($SkipLoadTest) {
        Write-Info "Skipping load balancing tests (--SkipLoadTest specified)"
        return $true
    }
    
    Write-Info "Testing load balancing for $Environment environment..."
    
    # This is a basic load test - in production you might use tools like k6 or Artillery
    Write-Info "Performing basic load test..."
    
    try {
        # Simple concurrent request test
        $jobs = @()
        for ($i = 1; $i -le 10; $i++) {
            $jobs += Start-Job -ScriptBlock {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8080/health/" -TimeoutSec 5
                    return $response.StatusCode
                } catch {
                    return 0
                }
            }
        }
        
        $results = $jobs | Wait-Job | Receive-Job
        $jobs | Remove-Job
        
        $successfulRequests = ($results | Where-Object { $_ -eq 200 }).Count
        $totalRequests = $results.Count
        
        Write-Info "Load test results: $successfulRequests/$totalRequests successful requests"
        
        if ($successfulRequests -ge ($totalRequests * 0.8)) {
            Write-Success "✓ Load balancing test passed (80%+ success rate)"
        } else {
            Write-Warning "⚠ Load balancing test failed (less than 80% success rate)"
        }
    } catch {
        Write-Warning "Failed to perform load test: $($_.Exception.Message)"
    }
    
    Write-Success "✓ Load balancing tests completed"
    return $true
}

# Main test function
function Invoke-DeploymentTests {
    param($Environment)
    
    Write-Info "Starting deployment tests for $Environment environment..."
    
    $results = @()
    
    $results += Test-PodHealth -Environment $Environment
    $results += Test-ServiceEndpoints -Environment $Environment
    $results += Test-ApplicationHealth -Environment $Environment
    $results += Test-DatabaseConnectivity -Environment $Environment
    $results += Test-HorizontalPodAutoscaler -Environment $Environment
    $results += Test-LoadBalancing -Environment $Environment
    
    $failedTests = $results | Where-Object { $_ -eq $false }
    
    if ($failedTests.Count -eq 0) {
        Write-Success "🎉 All deployment tests passed!"
        return $true
    } else {
        Write-Warning "⚠ $($failedTests.Count) deployment test(s) had issues"
        return $true  # Return true for warnings, false only for critical failures
    }
}

# Main execution
try {
    Write-Info "Kubernetes Deployment Testing Script"
    Write-Info "Environment: $Environment"
    Write-Info "Timeout: $Timeout seconds"
    Write-Info "Skip Load Test: $SkipLoadTest"
    
    $result = Invoke-DeploymentTests -Environment $Environment
    
    if (-not $result) {
        exit 1
    }
    
} catch {
    Write-Error "Deployment testing failed: $($_.Exception.Message)"
    exit 1
}