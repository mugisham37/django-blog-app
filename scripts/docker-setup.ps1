# Docker Setup Script for Fullstack Monolith (PowerShell)
# This script sets up the complete Docker environment on Windows

param(
    [switch]$Help,
    [switch]$Clean,
    [switch]$Prod
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    if (-not (Test-Command "docker-compose")) {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Create necessary directories
function New-Directories {
    Write-Status "Creating necessary directories..."
    
    $directories = @(
        "infrastructure\nginx\ssl",
        "infrastructure\database",
        "infrastructure\redis",
        "monitoring\prometheus",
        "monitoring\grafana\provisioning",
        "monitoring\grafana\dashboards",
        "logs",
        "backups"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directories created"
}

# Setup environment files
function Set-Environment {
    Write-Status "Setting up environment files..."
    
    if (-not (Test-Path ".env.docker")) {
        if (Test-Path ".env.docker.example") {
            Copy-Item ".env.docker.example" ".env.docker"
            Write-Warning "Created .env.docker from example. Please update the values!"
        }
        else {
            Write-Error ".env.docker.example not found. Please create environment configuration."
            exit 1
        }
    }
    else {
        Write-Success ".env.docker already exists"
    }
}

# Build Docker images
function Build-Images {
    Write-Status "Building Docker images..."
    
    # Build development images
    docker-compose build --no-cache
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker images"
        exit 1
    }
    
    Write-Success "Docker images built successfully"
}

# Initialize database
function Initialize-Database {
    Write-Status "Initializing database..."
    
    # Start only database and redis first
    docker-compose up -d postgres redis
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start database services"
        exit 1
    }
    
    # Wait for database to be ready
    Write-Status "Waiting for database to be ready..."
    Start-Sleep -Seconds 10
    
    # Run migrations
    docker-compose run --rm django-api python manage.py migrate
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to run database migrations"
        exit 1
    }
    
    Write-Success "Database initialized"
}

# Create superuser
function New-Superuser {
    Write-Status "Creating Django superuser..."
    
    Write-Host "Please create a Django superuser account:"
    docker-compose run --rm django-api python manage.py createsuperuser
    
    Write-Success "Superuser created"
}

# Start all services
function Start-Services {
    Write-Status "Starting all services..."
    
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services"
        exit 1
    }
    
    Write-Status "Waiting for services to start..."
    Start-Sleep -Seconds 15
    
    # Check service health
    Test-ServicesHealth
}

# Check services health
function Test-ServicesHealth {
    Write-Status "Checking services health..."
    
    # Check Django API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health/" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Django API is healthy"
        }
    }
    catch {
        Write-Warning "Django API is not responding"
    }
    
    # Check Next.js
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Next.js is healthy"
        }
    }
    catch {
        Write-Warning "Next.js is not responding"
    }
    
    # Check Nginx
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Nginx is healthy"
        }
    }
    catch {
        Write-Warning "Nginx is not responding"
    }
}

# Show service URLs
function Show-URLs {
    Write-Success "Docker setup completed successfully!"
    Write-Host ""
    Write-Host "Available services:"
    Write-Host "  🌐 Web Application:     http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🔧 Django API:         http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📊 Django Admin:       http://localhost:8000/admin/" -ForegroundColor Cyan
    Write-Host "  🔄 Nginx Proxy:        http://localhost" -ForegroundColor Cyan
    Write-Host "  📧 Mailhog (Dev):      http://localhost:8025" -ForegroundColor Cyan
    Write-Host "  🗄️  Adminer (DB):       http://localhost:8080" -ForegroundColor Cyan
    Write-Host "  📊 Redis Commander:    http://localhost:8081" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view logs: docker-compose logs -f"
    Write-Host "To stop services: docker-compose down"
    Write-Host "To restart services: docker-compose restart"
    Write-Host ""
    Write-Warning "Don't forget to update .env.docker with your actual configuration!"
}

# Cleanup function
function Stop-Services {
    Write-Status "Cleaning up..."
    try {
        docker-compose down | Out-Null
    }
    catch {
        # Ignore errors during cleanup
    }
}

# Show help
function Show-Help {
    Write-Host "Docker Setup Script for Fullstack Monolith"
    Write-Host ""
    Write-Host "Usage: .\scripts\docker-setup.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help          Show this help message"
    Write-Host "  -Clean         Clean up Docker resources before setup"
    Write-Host "  -Prod          Setup for production environment"
    Write-Host ""
}

# Main execution
function Main {
    Write-Host "🐳 Docker Setup for Fullstack Monolith" -ForegroundColor Magenta
    Write-Host "======================================" -ForegroundColor Magenta
    Write-Host ""
    
    Test-Prerequisites
    New-Directories
    Set-Environment
    Build-Images
    Initialize-Database
    
    # Ask if user wants to create superuser
    $createSuperuser = Read-Host "Do you want to create a Django superuser? (y/n)"
    if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
        New-Superuser
    }
    
    Start-Services
    Show-URLs
}

# Handle script arguments
if ($Help) {
    Show-Help
    exit 0
}

if ($Clean) {
    Write-Status "Cleaning up existing Docker resources..."
    try {
        docker-compose down --volumes --remove-orphans | Out-Null
        docker system prune -f | Out-Null
    }
    catch {
        # Ignore errors during cleanup
    }
    Write-Success "Cleanup completed"
}

if ($Prod) {
    Write-Status "Setting up production environment..."
    $env:COMPOSE_FILE = "docker-compose.prod.yml"
}

# Set error handling
$ErrorActionPreference = "Stop"

try {
    Main
}
catch {
    Write-Error "Setup failed: $($_.Exception.Message)"
    Stop-Services
    exit 1
}
finally {
    # Reset error handling
    $ErrorActionPreference = "Continue"
}