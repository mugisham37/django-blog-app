#!/bin/bash

# Docker Setup Script for Fullstack Monolith
# This script sets up the complete Docker environment

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p infrastructure/nginx/ssl
    mkdir -p infrastructure/database
    mkdir -p infrastructure/redis
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning
    mkdir -p monitoring/grafana/dashboards
    mkdir -p logs
    mkdir -p backups
    
    print_success "Directories created"
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    if [ ! -f .env.docker ]; then
        if [ -f .env.docker.example ]; then
            cp .env.docker.example .env.docker
            print_warning "Created .env.docker from example. Please update the values!"
        else
            print_error ".env.docker.example not found. Please create environment configuration."
            exit 1
        fi
    else
        print_success ".env.docker already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build development images
    docker-compose build --no-cache
    
    print_success "Docker images built successfully"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Start only database and redis first
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose run --rm django-api python manage.py migrate
    
    print_success "Database initialized"
}

# Create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    
    echo "Please create a Django superuser account:"
    docker-compose run --rm django-api python manage.py createsuperuser
    
    print_success "Superuser created"
}

# Start all services
start_services() {
    print_status "Starting all services..."
    
    docker-compose up -d
    
    print_status "Waiting for services to start..."
    sleep 15
    
    # Check service health
    check_services_health
}

# Check services health
check_services_health() {
    print_status "Checking services health..."
    
    # Check Django API
    if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
        print_success "Django API is healthy"
    else
        print_warning "Django API is not responding"
    fi
    
    # Check Next.js
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        print_success "Next.js is healthy"
    else
        print_warning "Next.js is not responding"
    fi
    
    # Check Nginx
    if curl -f http://localhost/health >/dev/null 2>&1; then
        print_success "Nginx is healthy"
    else
        print_warning "Nginx is not responding"
    fi
}

# Show service URLs
show_urls() {
    print_success "Docker setup completed successfully!"
    echo ""
    echo "Available services:"
    echo "  🌐 Web Application:     http://localhost:3000"
    echo "  🔧 Django API:         http://localhost:8000"
    echo "  📊 Django Admin:       http://localhost:8000/admin/"
    echo "  🔄 Nginx Proxy:        http://localhost"
    echo "  📧 Mailhog (Dev):      http://localhost:8025"
    echo "  🗄️  Adminer (DB):       http://localhost:8080"
    echo "  📊 Redis Commander:    http://localhost:8081"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
    echo "To restart services: docker-compose restart"
    echo ""
    print_warning "Don't forget to update .env.docker with your actual configuration!"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose down >/dev/null 2>&1 || true
}

# Main execution
main() {
    echo "🐳 Docker Setup for Fullstack Monolith"
    echo "======================================"
    echo ""
    
    # Set trap for cleanup on exit
    trap cleanup EXIT
    
    check_prerequisites
    create_directories
    setup_environment
    build_images
    init_database
    
    # Ask if user wants to create superuser
    read -p "Do you want to create a Django superuser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_superuser
    fi
    
    start_services
    show_urls
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Docker Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --clean        Clean up Docker resources before setup"
        echo "  --prod         Setup for production environment"
        echo ""
        exit 0
        ;;
    --clean)
        print_status "Cleaning up existing Docker resources..."
        docker-compose down --volumes --remove-orphans >/dev/null 2>&1 || true
        docker system prune -f >/dev/null 2>&1 || true
        print_success "Cleanup completed"
        main
        ;;
    --prod)
        print_status "Setting up production environment..."
        export COMPOSE_FILE="docker-compose.prod.yml"
        main
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac