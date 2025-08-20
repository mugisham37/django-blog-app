# Production Deployment Script for Windows/PowerShell
# Comprehensive deployment orchestration with health checks and rollback

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Rollback = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$RollbackVersion = ""
)

# Configuration
$ErrorActionPreference = "Stop"
$LogFile = "logs/deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$DeploymentTimeout = 1800  # 30 minutes
$HealthCheckRetries = 10
$HealthCheckInterval = 30

# Ensure logs directory exists
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

# Error handling
function Write-Error-Exit {
    param([string]$Message)
    Write-Log $Message "ERROR"
    exit 1
}

# Success logging
function Write-Success {
    param([string]$Message)
    Write-Log $Message "SUCCESS"
}

# Warning logging
function Write-Warning {
    param([string]$Message)
    Write-Log $Message "WARNING"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking deployment prerequisites..."
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Exit "Docker is not installed or not in PATH"
    }
    
    # Check Docker Compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error-Exit "Docker Compose is not installed or not in PATH"
    }
    
    # Check required environment variables
    $requiredVars = @(
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "ELASTIC_PASSWORD",
        "DOMAIN_NAME"
    )
    
    foreach ($var in $requiredVars) {
        if (-not (Get-ChildItem Env:$var -ErrorAction SilentlyContinue)) {
            Write-Error-Exit "Required environment variable $var is not set"
        }
    }
    
    # Check disk space
    $freeSpace = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB
    if ($freeSpace -lt 10) {
        Write-Error-Exit "Insufficient disk space. At least 10GB required, found $([math]::Round($freeSpace, 2))GB"
    }
    
    Write-Success "Prerequisites check passed"
}

# Backup current deployment
function Backup-CurrentDeployment {
    Write-Log "Creating backup of current deployment..."
    
    $backupDir = "backups/deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup database
    Write-Log "Backing up database..."
    docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec -T postgres-primary pg_dump -U $env:POSTGRES_USER -d $env:POSTGRES_DB | gzip > "$backupDir/database-backup.sql.gz"
    
    # Backup configuration files
    Write-Log "Backing up configuration files..."
    Copy-Item -Path ".env.production" -Destination "$backupDir/" -ErrorAction SilentlyContinue
    Copy-Item -Path "docker-compose.prod.yml" -Destination "$backupDir/" -ErrorAction SilentlyContinue
    
    # Save current image versions
    docker images --format "table {{.Repository}}:{{.Tag}}" | Out-File "$backupDir/current-images.txt"
    
    Write-Success "Backup created at $backupDir"
    return $backupDir
}

# Deploy infrastructure services
function Deploy-Infrastructure {
    Write-Log "Deploying infrastructure services..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would deploy infrastructure services"
        return
    }
    
    # Deploy database cluster
    Write-Log "Deploying database cluster..."
    docker-compose -f infrastructure/database/production/docker-compose.prod.yml up -d
    
    # Deploy Redis cluster
    Write-Log "Deploying Redis cluster..."
    docker-compose -f infrastructure/cache/production/redis-cluster.yml up -d
    
    # Deploy monitoring stack
    Write-Log "Deploying monitoring stack..."
    docker-compose -f infrastructure/monitoring/production/performance-monitoring.yml up -d
    
    # Deploy logging stack
    Write-Log "Deploying logging stack..."
    docker-compose -f infrastructure/logging/production/docker-compose.logging.yml up -d
    
    # Deploy security services
    Write-Log "Deploying security services..."
    docker-compose -f infrastructure/security/production/security-config.yml up -d
    
    Write-Success "Infrastructure services deployed"
}

# Deploy application services
function Deploy-Applications {
    Write-Log "Deploying application services..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would deploy application services"
        return
    }
    
    # Build and deploy Django API
    Write-Log "Building and deploying Django API..."
    docker build -t django-api:$Version apps/api/
    docker tag django-api:$Version django-api:latest
    
    # Build and deploy Next.js Web App
    Write-Log "Building and deploying Next.js Web App..."
    docker build -t nextjs-web:$Version apps/web/
    docker tag nextjs-web:$Version nextjs-web:latest
    
    # Deploy CDN and reverse proxy
    Write-Log "Deploying CDN and reverse proxy..."
    docker-compose -f infrastructure/cache/production/cdn-config.yml up -d
    
    # Deploy main application stack
    Write-Log "Deploying main application stack..."
    docker-compose -f docker-compose.prod.yml up -d
    
    Write-Success "Application services deployed"
}

# Run database migrations
function Run-DatabaseMigrations {
    Write-Log "Running database migrations..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would run database migrations"
        return
    }
    
    # Wait for database to be ready
    $retries = 0
    do {
        $retries++
        Write-Log "Waiting for database to be ready (attempt $retries)..."
        Start-Sleep -Seconds 10
        $dbReady = docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec -T postgres-primary pg_isready -U $env:POSTGRES_USER
    } while (-not $dbReady -and $retries -lt 30)
    
    if (-not $dbReady) {
        Write-Error-Exit "Database failed to become ready"
    }
    
    # Run Django migrations
    docker-compose -f docker-compose.prod.yml exec -T django-api python manage.py migrate --noinput
    
    # Collect static files
    docker-compose -f docker-compose.prod.yml exec -T django-api python manage.py collectstatic --noinput
    
    Write-Success "Database migrations completed"
}

# Health check function
function Test-ServiceHealth {
    param([string]$ServiceName, [string]$HealthUrl, [int]$ExpectedStatus = 200)
    
    Write-Log "Checking health of $ServiceName..."
    
    $retries = 0
    do {
        $retries++
        try {
            $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 30
            if ($response.StatusCode -eq $ExpectedStatus) {
                Write-Success "$ServiceName is healthy"
                return $true
            }
        }
        catch {
            Write-Log "Health check failed for $ServiceName (attempt $retries): $($_.Exception.Message)"
        }
        
        if ($retries -lt $HealthCheckRetries) {
            Start-Sleep -Seconds $HealthCheckInterval
        }
    } while ($retries -lt $HealthCheckRetries)
    
    Write-Error-Exit "$ServiceName failed health check after $HealthCheckRetries attempts"
}

# Comprehensive health checks
function Test-DeploymentHealth {
    Write-Log "Running comprehensive health checks..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would run health checks"
        return
    }
    
    # Check database
    Test-ServiceHealth "Database" "http://localhost:5432" -ExpectedStatus 0  # pg_isready returns 0 for success
    
    # Check Redis
    $redisHealth = docker-compose -f infrastructure/cache/production/redis-cluster.yml exec -T redis-master redis-cli ping
    if ($redisHealth -ne "PONG") {
        Write-Error-Exit "Redis health check failed"
    }
    Write-Success "Redis is healthy"
    
    # Check Django API
    Test-ServiceHealth "Django API" "https://$env:DOMAIN_NAME/api/health"
    
    # Check Next.js Web App
    Test-ServiceHealth "Next.js Web App" "https://$env:DOMAIN_NAME"
    
    # Check monitoring services
    Test-ServiceHealth "Prometheus" "http://localhost:9090/-/healthy"
    Test-ServiceHealth "Grafana" "http://localhost:3001/api/health"
    
    # Check logging services
    Test-ServiceHealth "Elasticsearch" "http://localhost:9200/_cluster/health"
    Test-ServiceHealth "Kibana" "http://localhost:5601/api/status"
    
    Write-Success "All health checks passed"
}

# Rollback function
function Start-Rollback {
    param([string]$BackupDir, [string]$RollbackVersion)
    
    Write-Log "Starting rollback process..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would rollback deployment"
        return
    }
    
    # Stop current services
    Write-Log "Stopping current services..."
    docker-compose -f docker-compose.prod.yml down
    
    # Restore database if backup exists
    if (Test-Path "$BackupDir/database-backup.sql.gz") {
        Write-Log "Restoring database from backup..."
        Get-Content "$BackupDir/database-backup.sql.gz" | docker-compose -f infrastructure/database/production/docker-compose.prod.yml exec -T postgres-primary psql -U $env:POSTGRES_USER -d $env:POSTGRES_DB
    }
    
    # Restore configuration files
    if (Test-Path "$BackupDir/.env.production") {
        Copy-Item -Path "$BackupDir/.env.production" -Destination ".env.production"
    }
    
    # Rollback to previous version
    if ($RollbackVersion) {
        Write-Log "Rolling back to version $RollbackVersion..."
        docker tag django-api:$RollbackVersion django-api:latest
        docker tag nextjs-web:$RollbackVersion nextjs-web:latest
    }
    
    # Restart services
    Write-Log "Restarting services with rollback version..."
    docker-compose -f docker-compose.prod.yml up -d
    
    Write-Success "Rollback completed"
}

# Main deployment function
function Start-Deployment {
    Write-Log "Starting production deployment..."
    Write-Log "Environment: $Environment"
    Write-Log "Version: $Version"
    Write-Log "Dry Run: $DryRun"
    
    $backupDir = $null
    
    try {
        # Check prerequisites
        Test-Prerequisites
        
        # Create backup
        if (-not $DryRun) {
            $backupDir = Backup-CurrentDeployment
        }
        
        # Deploy infrastructure
        Deploy-Infrastructure
        
        # Deploy applications
        Deploy-Applications
        
        # Run database migrations
        Run-DatabaseMigrations
        
        # Health checks
        if (-not $SkipValidation) {
            Test-DeploymentHealth
        }
        
        # Run deployment validation script
        if (-not $SkipValidation -and -not $DryRun) {
            Write-Log "Running deployment validation..."
            & "infrastructure/deployment/production/deployment-validation.sh"
        }
        
        Write-Success "Production deployment completed successfully!"
        Write-Log "Deployment log: $LogFile"
        
        if ($backupDir) {
            Write-Log "Backup location: $backupDir"
        }
        
    }
    catch {
        Write-Error-Exit "Deployment failed: $($_.Exception.Message)"
        
        # Automatic rollback on failure
        if ($backupDir -and -not $DryRun) {
            Write-Log "Initiating automatic rollback..."
            Start-Rollback $backupDir $RollbackVersion
        }
    }
}

# Handle rollback request
if ($Rollback) {
    if (-not $RollbackVersion) {
        Write-Error-Exit "Rollback version must be specified with -RollbackVersion parameter"
    }
    
    $latestBackup = Get-ChildItem -Path "backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($latestBackup) {
        Start-Rollback $latestBackup.FullName $RollbackVersion
    } else {
        Write-Error-Exit "No backup found for rollback"
    }
} else {
    # Normal deployment
    Start-Deployment
}

Write-Log "Script execution completed."