#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Setup script for code quality tools and configurations

.DESCRIPTION
    This script installs and configures all code quality tools including:
    - ESLint and Prettier for JavaScript/TypeScript
    - Black, isort, and Flake8 for Python
    - Pre-commit hooks
    - SonarQube scanner
    - Security scanning tools

.PARAMETER SkipPython
    Skip Python tool installation

.PARAMETER SkipNode
    Skip Node.js tool installation

.PARAMETER SkipPreCommit
    Skip pre-commit hooks setup

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\setup-code-quality.ps1
    
.EXAMPLE
    .\setup-code-quality.ps1 -SkipPython -Verbose
#>

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipPreCommit,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Enable verbose output if requested
if ($Verbose) {
    $VerbosePreference = "Continue"
}

# Color functions for output
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

# Check if command exists
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

# Main setup function
function Start-CodeQualitySetup {
    Write-Step "Code Quality Tools Setup"
    Write-Info "Setting up code quality tools for the monorepo..."

    # Check prerequisites
    Test-Prerequisites

    # Install Node.js dependencies
    if (-not $SkipNode) {
        Install-NodeDependencies
    }

    # Install Python dependencies
    if (-not $SkipPython) {
        Install-PythonDependencies
    }

    # Setup pre-commit hooks
    if (-not $SkipPreCommit) {
        Setup-PreCommitHooks
    }

    # Setup SonarQube scanner
    Setup-SonarQubeScanner

    # Validate installation
    Test-Installation

    Write-Step "Setup Complete"
    Write-Success "Code quality tools have been successfully configured!"
    Write-Info "Run 'npm run validate' to test all tools"
}

function Test-Prerequisites {
    Write-Step "Checking Prerequisites"

    # Check Node.js
    if (Test-Command "node") {
        $nodeVersion = node --version
        Write-Success "Node.js found: $nodeVersion"
    }
    else {
        Write-Error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    }

    # Check npm
    if (Test-Command "npm") {
        $npmVersion = npm --version
        Write-Success "npm found: $npmVersion"
    }
    else {
        Write-Error "npm is not installed. Please install npm first."
        exit 1
    }

    # Check Python
    if (Test-Command "python") {
        $pythonVersion = python --version
        Write-Success "Python found: $pythonVersion"
    }
    elseif (Test-Command "python3") {
        $pythonVersion = python3 --version
        Write-Success "Python3 found: $pythonVersion"
        # Create alias for consistency
        Set-Alias -Name python -Value python3 -Scope Global
    }
    else {
        Write-Warning "Python is not installed. Python tools will be skipped."
        $script:SkipPython = $true
    }

    # Check pip
    if (-not $SkipPython) {
        if (Test-Command "pip") {
            $pipVersion = pip --version
            Write-Success "pip found: $pipVersion"
        }
        else {
            Write-Warning "pip is not installed. Python tools will be skipped."
            $script:SkipPython = $true
        }
    }

    # Check Git
    if (Test-Command "git") {
        $gitVersion = git --version
        Write-Success "Git found: $gitVersion"
    }
    else {
        Write-Error "Git is not installed. Please install Git first."
        exit 1
    }
}

function Install-NodeDependencies {
    Write-Step "Installing Node.js Dependencies"

    try {
        Write-Info "Installing npm dependencies..."
        npm install

        Write-Info "Installing additional ESLint plugins..."
        npm install --save-dev `
            eslint-plugin-security `
            eslint-plugin-sonarjs `
            eslint-plugin-import `
            eslint-plugin-jsx-a11y `
            eslint-plugin-react `
            eslint-plugin-react-hooks

        Write-Info "Installing Prettier plugins..."
        npm install --save-dev `
            "@trivago/prettier-plugin-sort-imports" `
            prettier-plugin-tailwindcss

        Write-Info "Installing additional development tools..."
        npm install --save-dev `
            markdownlint-cli `
            validate-package-name `
            chalk

        Write-Success "Node.js dependencies installed successfully"
    }
    catch {
        Write-Error "Failed to install Node.js dependencies: $_"
        exit 1
    }
}

function Install-PythonDependencies {
    Write-Step "Installing Python Dependencies"

    try {
        Write-Info "Upgrading pip..."
        python -m pip install --upgrade pip

        Write-Info "Installing code formatting tools..."
        python -m pip install black isort

        Write-Info "Installing linting tools..."
        python -m pip install flake8 flake8-bugbear flake8-comprehensions flake8-docstrings flake8-import-order flake8-quotes flake8-security flake8-django pep8-naming

        Write-Info "Installing type checking tools..."
        python -m pip install mypy django-stubs djangorestframework-stubs types-requests types-redis types-python-dateutil

        Write-Info "Installing security tools..."
        python -m pip install bandit safety

        Write-Info "Installing testing tools..."
        python -m pip install pytest pytest-cov pytest-django factory-boy faker

        Write-Info "Installing additional quality tools..."
        python -m pip install ruff vulture

        Write-Success "Python dependencies installed successfully"
    }
    catch {
        Write-Error "Failed to install Python dependencies: $_"
        Write-Warning "You may need to install Python dependencies manually"
    }
}

function Setup-PreCommitHooks {
    Write-Step "Setting up Pre-commit Hooks"

    try {
        Write-Info "Installing pre-commit..."
        python -m pip install pre-commit

        Write-Info "Installing pre-commit hooks..."
        pre-commit install

        Write-Info "Installing commit-msg hook..."
        pre-commit install --hook-type commit-msg

        Write-Info "Running pre-commit on all files (this may take a while)..."
        pre-commit run --all-files || Write-Warning "Some pre-commit checks failed - this is normal for initial setup"

        Write-Success "Pre-commit hooks configured successfully"
    }
    catch {
        Write-Error "Failed to setup pre-commit hooks: $_"
        Write-Warning "You may need to setup pre-commit hooks manually"
    }
}

function Setup-SonarQubeScanner {
    Write-Step "Setting up SonarQube Scanner"

    try {
        # Check if SonarQube scanner is already installed
        if (Test-Command "sonar-scanner") {
            Write-Success "SonarQube scanner already installed"
            return
        }

        Write-Info "SonarQube scanner not found. Please install it manually:"
        Write-Info "1. Download from: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/"
        Write-Info "2. Add to PATH environment variable"
        Write-Info "3. Configure sonar-project.properties (already created)"
        
        Write-Warning "SonarQube scanner installation skipped - manual setup required"
    }
    catch {
        Write-Warning "Could not setup SonarQube scanner: $_"
    }
}

function Test-Installation {
    Write-Step "Validating Installation"

    Write-Info "Running code quality validator..."
    try {
        node tools/code-quality-validator.js
        Write-Success "Code quality validation passed"
    }
    catch {
        Write-Warning "Code quality validation had issues - check the output above"
    }

    Write-Info "Testing ESLint..."
    try {
        npx eslint --version | Out-Null
        Write-Success "ESLint is working"
    }
    catch {
        Write-Error "ESLint is not working properly"
    }

    Write-Info "Testing Prettier..."
    try {
        npx prettier --version | Out-Null
        Write-Success "Prettier is working"
    }
    catch {
        Write-Error "Prettier is not working properly"
    }

    if (-not $SkipPython) {
        Write-Info "Testing Black..."
        try {
            python -m black --version | Out-Null
            Write-Success "Black is working"
        }
        catch {
            Write-Warning "Black is not working properly"
        }

        Write-Info "Testing isort..."
        try {
            python -m isort --version | Out-Null
            Write-Success "isort is working"
        }
        catch {
            Write-Warning "isort is not working properly"
        }

        Write-Info "Testing Flake8..."
        try {
            python -m flake8 --version | Out-Null
            Write-Success "Flake8 is working"
        }
        catch {
            Write-Warning "Flake8 is not working properly"
        }
    }

    if (-not $SkipPreCommit) {
        Write-Info "Testing pre-commit..."
        try {
            pre-commit --version | Out-Null
            Write-Success "Pre-commit is working"
        }
        catch {
            Write-Warning "Pre-commit is not working properly"
        }
    }
}

function Show-Usage {
    Write-Info "Code Quality Tools Setup Complete!"
    Write-Info ""
    Write-Info "Available commands:"
    Write-Info "  npm run lint          - Run all linting"
    Write-Info "  npm run lint:web      - Run JavaScript/TypeScript linting"
    Write-Info "  npm run lint:api      - Run Python linting"
    Write-Info "  npm run format        - Format all code"
    Write-Info "  npm run format:web    - Format JavaScript/TypeScript code"
    Write-Info "  npm run format:api    - Format Python code"
    Write-Info "  npm run validate      - Run all quality checks"
    Write-Info ""
    Write-Info "Pre-commit hooks are now active and will run on every commit."
    Write-Info "To skip hooks temporarily, use: git commit --no-verify"
    Write-Info ""
    Write-Info "For more information, see docs/CODE_REVIEW_GUIDELINES.md"
}

# Main execution
try {
    Start-CodeQualitySetup
    Show-Usage
}
catch {
    Write-Error "Setup failed: $_"
    exit 1
}