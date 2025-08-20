# Development Environment Setup Script for Windows
# This script sets up the complete development environment for the fullstack monolith

param(
    [switch]$SkipDependencies,
    [switch]$SkipDatabase,
    [switch]$SkipDocker,
    [switch]$Force,
    [string]$Environment = "development"
)

Write-Host "🚀 Setting up development environment..." -ForegroundColor Green

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to run command with error handling
function Invoke-SafeCommand {
    param(
        [string]$Command,
        [string]$Description,
        [switch]$ContinueOnError
    )
    
    Write-Host "📦 $Description..." -ForegroundColor Yellow
    
    try {
        Invoke-Expression $Command
        if ($LASTEXITCODE -ne 0 -and -not $ContinueOnError) {
            throw "Command failed with exit code $LASTEXITCODE"
        }
        Write-Host "✅ $Description completed" -ForegroundColor Green
    } catch {
        Write-Host "❌ $Description failed: $_" -ForegroundColor Red
        if (-not $ContinueOnError) {
            exit 1
        }
    }
}

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Cyan

$prerequisites = @{
    "node" = "Node.js"
    "npm" = "npm"
    "python" = "Python"
    "pip" = "pip"
    "git" = "Git"
}

$missingPrereqs = @()

foreach ($cmd in $prerequisites.Keys) {
    if (-not (Test-Command $cmd)) {
        $missingPrereqs += $prerequisites[$cmd]
        Write-Host "❌ $($prerequisites[$cmd]) not found" -ForegroundColor Red
    } else {
        Write-Host "✅ $($prerequisites[$cmd]) found" -ForegroundColor Green
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-Host "❌ Missing prerequisites: $($missingPrereqs -join ', ')" -ForegroundColor Red
    Write-Host "Please install the missing prerequisites and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check optional tools
Write-Host "🔍 Checking optional tools..." -ForegroundColor Cyan

$optionalTools = @{
    "docker" = "Docker"
    "docker-compose" = "Docker Compose"
    "psql" = "PostgreSQL Client"
}

foreach ($cmd in $optionalTools.Keys) {
    if (Test-Command $cmd) {
        Write-Host "✅ $($optionalTools[$cmd]) found" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $($optionalTools[$cmd]) not found (optional)" -ForegroundColor Yellow
    }
}

# Install dependencies
if (-not $SkipDependencies) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
    
    # Install root dependencies
    Invoke-SafeCommand "npm install" "Installing root npm dependencies"
    
    # Install Python dependencies
    if (Test-Path "requirements.txt") {
        Invoke-SafeCommand "pip install -r requirements.txt" "Installing Python dependencies"
    }
    
    # Install API dependencies
    if (Test-Path "apps/api/requirements") {
        Invoke-SafeCommand "pip install -r apps/api/requirements/development.txt" "Installing Django API dependencies"
    }
    
    # Install web app dependencies
    if (Test-Path "apps/web/package.json") {
        Push-Location "apps/web"
        Invoke-SafeCommand "npm install" "Installing Next.js web app dependencies"
        Pop-Location
    }
    
    # Install shared packages in development mode
    $packages = @("core", "auth", "cache", "database", "config")
    foreach ($package in $packages) {
        $packagePath = "packages/$package"
        if (Test-Path $packagePath) {
            Push-Location $packagePath
            Invoke-SafeCommand "pip install -e ." "Installing $package package in development mode"
            Pop-Location
        }
    }
    
    # Install API client package
    if (Test-Path "packages/api-client/package.json") {
        Push-Location "packages/api-client"
        Invoke-SafeCommand "npm install" "Installing API client package dependencies"
        Pop-Location
    }
}

# Setup environment files
Write-Host "⚙️ Setting up environment configuration..." -ForegroundColor Cyan

$envFiles = @{
    ".env" = ".env.example"
    "apps/api/.env" = ".env.$Environment.example"
    "apps/web/.env.local" = ".env.$Environment.example"
}

foreach ($envFile in $envFiles.Keys) {
    $exampleFile = $envFiles[$envFile]
    
    if (Test-Path $exampleFile) {
        if (-not (Test-Path $envFile) -or $Force) {
            Copy-Item $exampleFile $envFile
            Write-Host "✅ Created $envFile from $exampleFile" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $envFile already exists, skipping" -ForegroundColor Yellow
        }
    }
}

# Setup database
if (-not $SkipDatabase) {
    Write-Host "🗄️ Setting up database..." -ForegroundColor Cyan
    
    # Check if PostgreSQL is running
    if (Test-Command "psql") {
        try {
            # Try to connect to PostgreSQL
            $null = psql -U postgres -c "SELECT 1;" 2>$null
            Write-Host "✅ PostgreSQL is running" -ForegroundColor Green
            
            # Run database setup
            Push-Location "apps/api"
            Invoke-SafeCommand "python manage.py migrate" "Running database migrations"
            Invoke-SafeCommand "python tools/db-automation.py seed --env $Environment" "Seeding database with sample data" -ContinueOnError
            Pop-Location
            
        } catch {
            Write-Host "⚠️ PostgreSQL not accessible, skipping database setup" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ PostgreSQL client not found, skipping database setup" -ForegroundColor Yellow
    }
}

# Setup Docker (if available)
if (-not $SkipDocker -and (Test-Command "docker") -and (Test-Command "docker-compose")) {
    Write-Host "🐳 Setting up Docker environment..." -ForegroundColor Cyan
    
    try {
        # Check if Docker is running
        docker info | Out-Null
        
        # Build Docker images
        Invoke-SafeCommand "docker-compose build" "Building Docker images"
        
        Write-Host "✅ Docker environment ready" -ForegroundColor Green
        Write-Host "💡 Run 'docker-compose up' to start services" -ForegroundColor Cyan
        
    } catch {
        Write-Host "⚠️ Docker not running, skipping Docker setup" -ForegroundColor Yellow
    }
}

# Setup code quality tools
Write-Host "🔧 Setting up code quality tools..." -ForegroundColor Cyan

# Install pre-commit hooks
if (Test-Command "pre-commit") {
    Invoke-SafeCommand "pre-commit install" "Installing pre-commit hooks"
    Invoke-SafeCommand "pre-commit install --hook-type commit-msg" "Installing commit message hooks"
} else {
    Write-Host "⚠️ pre-commit not found, install with: pip install pre-commit" -ForegroundColor Yellow
}

# Setup IDE configuration
Write-Host "🔧 Setting up IDE configuration..." -ForegroundColor Cyan

# Create VS Code settings if not exists
$vscodeDir = ".vscode"
if (-not (Test-Path $vscodeDir)) {
    New-Item -ItemType Directory -Path $vscodeDir | Out-Null
}

$vscodeSettings = @{
    "settings.json" = @{
        "python.defaultInterpreterPath" = "./venv/Scripts/python.exe"
        "python.linting.enabled" = $true
        "python.linting.flake8Enabled" = $true
        "python.formatting.provider" = "black"
        "typescript.preferences.importModuleSpecifier" = "relative"
        "editor.formatOnSave" = $true
        "editor.codeActionsOnSave" = @{
            "source.organizeImports" = $true
        }
    }
    "extensions.json" = @{
        "recommendations" = @(
            "ms-python.python",
            "ms-python.flake8",
            "ms-python.black-formatter",
            "bradlc.vscode-tailwindcss",
            "esbenp.prettier-vscode",
            "ms-vscode.vscode-typescript-next"
        )
    }
}

foreach ($file in $vscodeSettings.Keys) {
    $filePath = "$vscodeDir/$file"
    if (-not (Test-Path $filePath) -or $Force) {
        $vscodeSettings[$file] | ConvertTo-Json -Depth 10 | Set-Content $filePath
        Write-Host "✅ Created $filePath" -ForegroundColor Green
    }
}

# Generate TypeScript types
Write-Host "🔄 Generating TypeScript types..." -ForegroundColor Cyan
Invoke-SafeCommand "python tools/type-generator.py" "Generating TypeScript types from Django models" -ContinueOnError

# Generate API client
Write-Host "🔄 Generating API client..." -ForegroundColor Cyan
Invoke-SafeCommand "python tools/api-client-generator.py" "Generating API client from Django REST framework" -ContinueOnError

# Create development scripts
Write-Host "📝 Creating development scripts..." -ForegroundColor Cyan

$devScripts = @{
    "dev.ps1" = @"
# Development server startup script
Write-Host "🚀 Starting development servers..." -ForegroundColor Green

# Start hot reload manager
node tools/hot-reload-config.js start
"@
    
    "test.ps1" = @"
# Test runner script
Write-Host "🧪 Running tests..." -ForegroundColor Green

# Run all tests
make test
"@
    
    "build.ps1" = @"
# Build script
Write-Host "🏗️ Building applications..." -ForegroundColor Green

# Build all applications
make build
"@
}

foreach ($script in $devScripts.Keys) {
    if (-not (Test-Path $script) -or $Force) {
        $devScripts[$script] | Set-Content $script
        Write-Host "✅ Created $script" -ForegroundColor Green
    }
}

# Final setup validation
Write-Host "🔍 Validating setup..." -ForegroundColor Cyan

$validationChecks = @(
    @{ Path = "node_modules"; Description = "Node.js dependencies" },
    @{ Path = "apps/web/node_modules"; Description = "Next.js dependencies" },
    @{ Path = "packages/types/src"; Description = "TypeScript types" },
    @{ Path = ".env"; Description = "Environment configuration" }
)

$setupValid = $true

foreach ($check in $validationChecks) {
    if (Test-Path $check.Path) {
        Write-Host "✅ $($check.Description) - OK" -ForegroundColor Green
    } else {
        Write-Host "❌ $($check.Description) - Missing" -ForegroundColor Red
        $setupValid = $false
    }
}

# Display next steps
Write-Host "`n🎉 Development environment setup completed!" -ForegroundColor Green

if ($setupValid) {
    Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review and update .env files with your configuration" -ForegroundColor White
    Write-Host "2. Start development servers: .\dev.ps1 or make dev" -ForegroundColor White
    Write-Host "3. Run tests: .\test.ps1 or make test" -ForegroundColor White
    Write-Host "4. Open your browser to:" -ForegroundColor White
    Write-Host "   - Next.js app: http://localhost:3000" -ForegroundColor White
    Write-Host "   - Django API: http://localhost:8000" -ForegroundColor White
    Write-Host "   - Django Admin: http://localhost:8000/admin" -ForegroundColor White
    
    Write-Host "`n🔧 Available commands:" -ForegroundColor Cyan
    Write-Host "- make dev          Start development servers" -ForegroundColor White
    Write-Host "- make test         Run all tests" -ForegroundColor White
    Write-Host "- make build        Build applications" -ForegroundColor White
    Write-Host "- make lint         Run code linting" -ForegroundColor White
    Write-Host "- make format       Format code" -ForegroundColor White
    Write-Host "- make docker-up    Start with Docker" -ForegroundColor White
    
} else {
    Write-Host "`n⚠️ Setup completed with some issues. Please review the errors above." -ForegroundColor Yellow
}

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "- Development guide: docs/development.md" -ForegroundColor White
Write-Host "- API documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- Component library: http://localhost:6006 (Storybook)" -ForegroundColor White