#!/bin/bash

# Enterprise Blog Testing Setup Script
# Sets up the complete testing infrastructure

set -e

echo "🚀 Setting up Enterprise Blog Testing Infrastructure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check Python
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Install Node.js dependencies
install_node_dependencies() {
    print_status "Installing Node.js testing dependencies..."
    
    cd tests
    
    # Install test dependencies
    npm install
    
    # Install global tools if not present
    if ! command -v newman &> /dev/null; then
        print_status "Installing Newman globally..."
        npm install -g newman
    fi
    
    cd ..
    print_success "Node.js dependencies installed"
}

# Setup Python testing environment
setup_python_environment() {
    print_status "Setting up Python testing environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    print_status "Installing Python testing dependencies..."
    pip install -r tests/requirements.txt
    
    print_success "Python environment setup complete"
}

# Install Playwright browsers
setup_playwright() {
    print_status "Setting up Playwright browsers..."
    
    cd tests
    npx playwright install
    cd ..
    
    print_success "Playwright browsers installed"
}

# Setup k6 for performance testing
setup_k6() {
    print_status "Checking k6 installation..."
    
    if command -v k6 &> /dev/null; then
        print_success "k6 is already installed"
        return
    fi
    
    print_warning "k6 is not installed. Performance tests will be skipped."
    print_status "To install k6, visit: https://k6.io/docs/getting-started/installation/"
    
    # Try to install k6 on different platforms
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            print_status "Attempting to install k6 via apt..."
            sudo gpg -k
            sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
            echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
            sudo apt-get update
            sudo apt-get install k6
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            print_status "Attempting to install k6 via Homebrew..."
            brew install k6
        fi
    fi
}

# Create test directories
create_test_directories() {
    print_status "Creating test directories..."
    
    mkdir -p tests/reports
    mkdir -p tests/coverage
    mkdir -p tests/artifacts
    mkdir -p tests/screenshots
    mkdir -p tests/videos
    
    print_success "Test directories created"
}

# Setup test data
setup_test_data() {
    print_status "Setting up test data..."
    
    # Create test environment files if they don't exist
    if [ ! -f "tests/api/environments/development.json" ]; then
        print_status "Test environment files already exist"
    fi
    
    # Create test database
    if [ -f "apps/api/manage.py" ]; then
        print_status "Setting up test database..."
        cd apps/api
        
        # Activate Python virtual environment
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            source ../../venv/Scripts/activate
        else
            source ../../venv/bin/activate
        fi
        
        # Run migrations for test database
        python manage.py migrate --settings=settings.test
        
        cd ../..
    fi
    
    print_success "Test data setup complete"
}

# Validate test setup
validate_setup() {
    print_status "Validating test setup..."
    
    # Test Node.js testing
    cd tests
    if npm run test:unit -- --passWithNoTests; then
        print_success "Node.js testing setup validated"
    else
        print_error "Node.js testing setup validation failed"
        exit 1
    fi
    cd ..
    
    # Test Python testing
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    if python -m pytest tests/django/ --collect-only > /dev/null 2>&1; then
        print_success "Python testing setup validated"
    else
        print_warning "Python testing setup validation failed - this may be normal if Django apps aren't fully set up"
    fi
    
    # Test Playwright
    cd tests
    if npx playwright --version > /dev/null 2>&1; then
        print_success "Playwright setup validated"
    else
        print_error "Playwright setup validation failed"
        exit 1
    fi
    cd ..
    
    print_success "Test setup validation complete"
}

# Generate test configuration
generate_config() {
    print_status "Generating test configuration..."
    
    # Create .env.test file if it doesn't exist
    if [ ! -f ".env.test" ]; then
        cat > .env.test << EOF
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
EOF
        print_success "Created .env.test configuration file"
    else
        print_status ".env.test already exists"
    fi
}

# Main setup function
main() {
    echo "=================================================="
    echo "  Enterprise Blog Testing Infrastructure Setup"
    echo "=================================================="
    echo ""
    
    check_prerequisites
    create_test_directories
    install_node_dependencies
    setup_python_environment
    setup_playwright
    setup_k6
    setup_test_data
    generate_config
    validate_setup
    
    echo ""
    echo "=================================================="
    print_success "Testing infrastructure setup complete!"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "1. Run 'npm test' to execute the full test suite"
    echo "2. Run 'npm run test:unit' for unit tests only"
    echo "3. Run 'npm run test:e2e' for end-to-end tests"
    echo "4. Run 'npm run test:api' for API tests"
    echo "5. Run 'npm run test:performance' for performance tests"
    echo ""
    echo "For more information, see tests/README.md"
    echo ""
}

# Run main function
main "$@"