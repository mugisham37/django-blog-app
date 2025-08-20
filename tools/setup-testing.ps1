# Enterprise Blog Testing Setup Script (PowerShell)
# Sets up the complete testing infrastructure on Windows

param(
    [switch]$SkipK6,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
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

# Check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        $majorVersion = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
        if ($majorVersion -lt 18) {
            Write-Error "Node.js version 18+ is required. Current version: $nodeVersion"
            exit 1
        }
        Write-Status "Node.js version: $nodeVersion ✓"
    }
    catch {
        Write-Error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Status "Python version: $pythonVersion ✓"
    }
    catch {
        Write-Error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        Write-Status "npm version: $npmVersion ✓"
    }
    catch {
        Write-Error "npm is not installed. Please install npm first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Install Node.js dependencies
function Install-NodeDependencies {
    Write-Status "Installing Node.js testing dependencies..."
    
    Push-Location tests
    
    try {
        # Install test dependencies
        npm install
        
        # Install global tools if not present
        try {
            newman --version | Out-Null
            Write-Status "Newman is already installed ✓"
        }
        catch {
            Write-Status "Installing Newman globally..."
            npm install -g newman
        }
        
        Write-Success "Node.js dependencies installed"
    }
    finally {
        Pop-Location
    }
}

# Setup Python testing environment
function Set-PythonEnvironment {
    Write-Status "Setting up Python testing environment..."
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Status "Creating Python virtual environment..."
        python -m venv venv
    }
    
    # Activate virtual environment and install dependencies
    Write-Status "Activating virtual environment..."
    & "venv\Scripts\Activate.ps1"
    
    Write-Status "Installing Python testing dependencies..."
    pip install -r tests\requirements.txt
    
    Write-Success "Python environment setup complete"
}

# Install Playwright browsers
function Set-Playwright {
    Write-Status "Setting up Playwright browsers..."
    
    Push-Location tests
    
    try {
        npx playwright install
        Write-Success "Playwright browsers installed"
    }
    finally {
        Pop-Location
    }
}

# Setup k6 for performance testing
function Set-K6 {
    if ($SkipK6) {
        Write-Warning "Skipping k6 installation as requested"
        return
    }
    
    Write-Status "Checking k6 installation..."
    
    try {
        k6 version | Out-Null
        Write-Success "k6 is already installed ✓"
        return
    }
    catch {
        Write-Warning "k6 is not installed. Performance tests will be skipped."
        Write-Status "To install k6 on Windows:"
        Write-Host "1. Download from: https://github.com/grafana/k6/releases" -ForegroundColor Cyan
        Write-Host "2. Or use Chocolatey: choco install k6" -ForegroundColor Cyan
        Write-Host "3. Or use Scoop: scoop install k6" -ForegroundColor Cyan
        
        # Try to install via Chocolatey if available
        try {
            choco --version | Out-Null
            Write-Status "Attempting to install k6 via Chocolatey..."
            choco install k6 -y
            Write-Success "k6 installed via Chocolatey"
        }
        catch {
            # Try to install via Scoop if available
            try {
                scoop --version | Out-Null
                Write-Status "Attempting to install k6 via Scoop..."
                scoop install k6
                Write-Success "k6 installed via Scoop"
            }
            catch {
                Write-Warning "Could not auto-install k6. Please install manually."
            }
        }
    }
}

# Create test directories
function New-TestDirectories {
    Write-Status "Creating test directories..."
    
    $directories = @(
        "tests\reports",
        "tests\coverage",
        "tests\artifacts",
        "tests\screenshots",
        "tests\videos"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Test directories created"
}

# Setup test data
function Set-TestData {
    Write-Status "Setting up test data..."
    
    # Create test database if Django app exists
    if (Test-Path "apps\api\manage.py") {
        Write-Status "Setting up test database..."
        Push-Location "apps\api"
        
        try {
            # Activate Python virtual environment
            & "..\..\venv\Scripts\Activate.ps1"
            
            # Run migrations for test database
            python manage.py migrate --settings=settings.test
            
            Write-Success "Test database setup complete"
        }
        catch {
            Write-Warning "Could not setup test database - this may be normal if Django isn't fully configured"
        }
        finally {
            Pop-Location
        }
    }
    
    Write-Success "Test data setup complete"
}

# Validate test setup
function Test-Setup {
    Write-Status "Validating test setup..."
    
    # Test Node.js testing
    Push-Location tests
    
    try {
        npm run test:unit -- --passWithNoTests | Out-Null
        Write-Success "Node.js testing setup validated ✓"
    }
    catch {
        Write-Error "Node.js testing setup validation failed"
        exit 1
    }
    finally {
        Pop-Location
    }
    
    # Test Python testing
    try {
        & "venv\Scripts\Activate.ps1"
        python -m pytest tests\django\ --collect-only | Out-Null
        Write-Success "Python testing setup validated ✓"
    }
    catch {
        Write-Warning "Python testing setup validation failed - this may be normal if Django apps aren't fully set up"
    }
    
    # Test Playwright
    Push-Location tests
    
    try {
        npx playwright --version | Out-Null
        Write-Success "Playwright setup validated ✓"
    }
    catch {
        Write-Error "Playwright setup validation failed"
        exit 1
    }
    finally {
        Pop-Location
    }
    
    Write-Success "Test setup validation complete"
}

# Generate test configuration
function New-TestConfig {
    Write-Status "Generating test configuration..."
    
    # Create .env.test file if it doesn't exist
    if (-not (Test-Path ".env.test")) {
        $envContent = @"
# Test Environment Configuration
NODE_ENV=test
DJANGO_SETTINGS_MODULE=settings.test

# Database
DATABASE_URL=sqlite:///test.db
TEST_DATABASE_URL=sqlite:///test.db

# API Configuration
API_BASE_URL=http://localhost:8000/api/v1
WEB_BASE_URL=http://localhost:3000

# Authentication
JWT_SECRET_KEY=test-secret-key-change-in-production
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400

# Cache
CACHE_BACKEND=locmem://
REDIS_URL=redis://localhost:6379/1

# Email (for testing)
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

# Performance Testing
K6_VUS=10
K6_DURATION=5m
K6_BASE_URL=http://localhost:8000

# Coverage
COVERAGE_THRESHOLD=80
"@
        
        Set-Content -Path ".env.test" -Value $envContent
        Write-Success "Created .env.test configuration file"
    }
    else {
        Write-Status ".env.test already exists ✓"
    }
}

# Main setup function
function Main {
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  Enterprise Blog Testing Infrastructure Setup" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        Test-Prerequisites
        New-TestDirectories
        Install-NodeDependencies
        Set-PythonEnvironment
        Set-Playwright
        Set-K6
        Set-TestData
        New-TestConfig
        Test-Setup
        
        Write-Host ""
        Write-Host "==================================================" -ForegroundColor Green
        Write-Success "Testing infrastructure setup complete!"
        Write-Host "==================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Run 'npm test' to execute the full test suite" -ForegroundColor White
        Write-Host "2. Run 'npm run test:unit' for unit tests only" -ForegroundColor White
        Write-Host "3. Run 'npm run test:e2e' for end-to-end tests" -ForegroundColor White
        Write-Host "4. Run 'npm run test:api' for API tests" -ForegroundColor White
        Write-Host "5. Run 'npm run test:performance' for performance tests" -ForegroundColor White
        Write-Host ""
        Write-Host "For more information, see tests/README.md" -ForegroundColor Yellow
        Write-Host ""
    }
    catch {
        Write-Error "Setup failed: $($_.Exception.Message)"
        exit 1
    }
}

# Run main function
Main