#!/bin/bash
# Development Environment Setup Script for Unix/Linux/macOS
# This script sets up the complete development environment for the fullstack monolith

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKIP_DEPENDENCIES=false
SKIP_DATABASE=false
SKIP_DOCKER=false
FORCE=false
ENVIRONMENT="development"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-dependencies)
            SKIP_DEPENDENCIES=true
            shift
            ;;
        --skip-database)
            SKIP_DATABASE=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-dependencies    Skip dependency installation"
            echo "  --skip-database       Skip database setup"
            echo "  --skip-docker         Skip Docker setup"
            echo "  --force               Force overwrite existing files"
            echo "  --environment ENV     Set environment (default: development)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}🚀 Setting up development environment...${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    local continue_on_error="${3:-false}"
    
    echo -e "${YELLOW}📦 $description...${NC}"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $description completed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        if [[ "$continue_on_error" != "true" ]]; then
            exit 1
        fi
    fi
}

# Check prerequisites
echo -e "${CYAN}🔍 Checking prerequisites...${NC}"

prerequisites=("node:Node.js" "npm:npm" "python3:Python" "pip3:pip" "git:Git")
missing_prereqs=()

for prereq in "${prerequisites[@]}"; do
    IFS=':' read -r cmd name <<< "$prereq"
    if command_exists "$cmd"; then
        echo -e "${GREEN}✅ $name found${NC}"
    else
        missing_prereqs+=("$name")
        echo -e "${RED}❌ $name not found${NC}"
    fi
done

if [[ ${#missing_prereqs[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Missing prerequisites: ${missing_prereqs[*]}${NC}"
    echo -e "${YELLOW}Please install the missing prerequisites and run this script again.${NC}"
    exit 1
fi

# Check optional tools
echo -e "${CYAN}🔍 Checking optional tools...${NC}"

optional_tools=("docker:Docker" "docker-compose:Docker Compose" "psql:PostgreSQL Client")

for tool in "${optional_tools[@]}"; do
    IFS=':' read -r cmd name <<< "$tool"
    if command_exists "$cmd"; then
        echo -e "${GREEN}✅ $name found${NC}"
    else
        echo -e "${YELLOW}⚠️ $name not found (optional)${NC}"
    fi
done

# Install dependencies
if [[ "$SKIP_DEPENDENCIES" != "true" ]]; then
    echo -e "${CYAN}📦 Installing dependencies...${NC}"
    
    # Install root dependencies
    run_command "npm install" "Installing root npm dependencies"
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        run_command "pip3 install -r requirements.txt" "Installing Python dependencies"
    fi
    
    # Install API dependencies
    if [[ -d "apps/api/requirements" ]]; then
        run_command "pip3 install -r apps/api/requirements/development.txt" "Installing Django API dependencies"
    fi
    
    # Install web app dependencies
    if [[ -f "apps/web/package.json" ]]; then
        run_command "cd apps/web && npm install && cd ../.." "Installing Next.js web app dependencies"
    fi
    
    # Install shared packages in development mode
    packages=("core" "auth" "cache" "database" "config")
    for package in "${packages[@]}"; do
        package_path="packages/$package"
        if [[ -d "$package_path" ]]; then
            run_command "cd $package_path && pip3 install -e . && cd ../.." "Installing $package package in development mode"
        fi
    done
    
    # Install API client package
    if [[ -f "packages/api-client/package.json" ]]; then
        run_command "cd packages/api-client && npm install && cd ../.." "Installing API client package dependencies"
    fi
fi

# Setup environment files
echo -e "${CYAN}⚙️ Setting up environment configuration...${NC}"

declare -A env_files=(
    [".env"]=".env.example"
    ["apps/api/.env"]=".env.$ENVIRONMENT.example"
    ["apps/web/.env.local"]=".env.$ENVIRONMENT.example"
)

for env_file in "${!env_files[@]}"; do
    example_file="${env_files[$env_file]}"
    
    if [[ -f "$example_file" ]]; then
        if [[ ! -f "$env_file" || "$FORCE" == "true" ]]; then
            cp "$example_file" "$env_file"
            echo -e "${GREEN}✅ Created $env_file from $example_file${NC}"
        else
            echo -e "${YELLOW}⚠️ $env_file already exists, skipping${NC}"
        fi
    fi
done

# Setup database
if [[ "$SKIP_DATABASE" != "true" ]]; then
    echo -e "${CYAN}🗄️ Setting up database...${NC}"
    
    # Check if PostgreSQL is running
    if command_exists "psql"; then
        if psql -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PostgreSQL is running${NC}"
            
            # Run database setup
            run_command "cd apps/api && python3 manage.py migrate && cd ../.." "Running database migrations"
            run_command "python3 tools/db-automation.py seed --env $ENVIRONMENT" "Seeding database with sample data" true
            
        else
            echo -e "${YELLOW}⚠️ PostgreSQL not accessible, skipping database setup${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ PostgreSQL client not found, skipping database setup${NC}"
    fi
fi

# Setup Docker (if available)
if [[ "$SKIP_DOCKER" != "true" && $(command_exists "docker") && $(command_exists "docker-compose") ]]; then
    echo -e "${CYAN}🐳 Setting up Docker environment...${NC}"
    
    if docker info >/dev/null 2>&1; then
        # Build Docker images
        run_command "docker-compose build" "Building Docker images"
        
        echo -e "${GREEN}✅ Docker environment ready${NC}"
        echo -e "${CYAN}💡 Run 'docker-compose up' to start services${NC}"
        
    else
        echo -e "${YELLOW}⚠️ Docker not running, skipping Docker setup${NC}"
    fi
fi

# Setup code quality tools
echo -e "${CYAN}🔧 Setting up code quality tools...${NC}"

# Install pre-commit hooks
if command_exists "pre-commit"; then
    run_command "pre-commit install" "Installing pre-commit hooks"
    run_command "pre-commit install --hook-type commit-msg" "Installing commit message hooks"
else
    echo -e "${YELLOW}⚠️ pre-commit not found, install with: pip3 install pre-commit${NC}"
fi

# Setup IDE configuration
echo -e "${CYAN}🔧 Setting up IDE configuration...${NC}"

# Create VS Code settings if not exists
vscode_dir=".vscode"
mkdir -p "$vscode_dir"

# VS Code settings
if [[ ! -f "$vscode_dir/settings.json" || "$FORCE" == "true" ]]; then
    cat > "$vscode_dir/settings.json" << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "typescript.preferences.importModuleSpecifier": "relative",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
EOF
    echo -e "${GREEN}✅ Created $vscode_dir/settings.json${NC}"
fi

# VS Code extensions
if [[ ! -f "$vscode_dir/extensions.json" || "$FORCE" == "true" ]]; then
    cat > "$vscode_dir/extensions.json" << 'EOF'
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next"
    ]
}
EOF
    echo -e "${GREEN}✅ Created $vscode_dir/extensions.json${NC}"
fi

# Generate TypeScript types
echo -e "${CYAN}🔄 Generating TypeScript types...${NC}"
run_command "python3 tools/type-generator.py" "Generating TypeScript types from Django models" true

# Generate API client
echo -e "${CYAN}🔄 Generating API client...${NC}"
run_command "python3 tools/api-client-generator.py" "Generating API client from Django REST framework" true

# Create development scripts
echo -e "${CYAN}📝 Creating development scripts...${NC}"

# Development server startup script
if [[ ! -f "dev.sh" || "$FORCE" == "true" ]]; then
    cat > "dev.sh" << 'EOF'
#!/bin/bash
# Development server startup script
echo "🚀 Starting development servers..."

# Start hot reload manager
node tools/hot-reload-config.js start
EOF
    chmod +x "dev.sh"
    echo -e "${GREEN}✅ Created dev.sh${NC}"
fi

# Test runner script
if [[ ! -f "test.sh" || "$FORCE" == "true" ]]; then
    cat > "test.sh" << 'EOF'
#!/bin/bash
# Test runner script
echo "🧪 Running tests..."

# Run all tests
make test
EOF
    chmod +x "test.sh"
    echo -e "${GREEN}✅ Created test.sh${NC}"
fi

# Build script
if [[ ! -f "build.sh" || "$FORCE" == "true" ]]; then
    cat > "build.sh" << 'EOF'
#!/bin/bash
# Build script
echo "🏗️ Building applications..."

# Build all applications
make build
EOF
    chmod +x "build.sh"
    echo -e "${GREEN}✅ Created build.sh${NC}"
fi

# Final setup validation
echo -e "${CYAN}🔍 Validating setup...${NC}"

validation_checks=(
    "node_modules:Node.js dependencies"
    "apps/web/node_modules:Next.js dependencies"
    "packages/types/src:TypeScript types"
    ".env:Environment configuration"
)

setup_valid=true

for check in "${validation_checks[@]}"; do
    IFS=':' read -r path description <<< "$check"
    if [[ -e "$path" ]]; then
        echo -e "${GREEN}✅ $description - OK${NC}"
    else
        echo -e "${RED}❌ $description - Missing${NC}"
        setup_valid=false
    fi
done

# Display next steps
echo -e "\n${GREEN}🎉 Development environment setup completed!${NC}"

if [[ "$setup_valid" == "true" ]]; then
    echo -e "\n${CYAN}📋 Next steps:${NC}"
    echo -e "${NC}1. Review and update .env files with your configuration${NC}"
    echo -e "${NC}2. Start development servers: ./dev.sh or make dev${NC}"
    echo -e "${NC}3. Run tests: ./test.sh or make test${NC}"
    echo -e "${NC}4. Open your browser to:${NC}"
    echo -e "${NC}   - Next.js app: http://localhost:3000${NC}"
    echo -e "${NC}   - Django API: http://localhost:8000${NC}"
    echo -e "${NC}   - Django Admin: http://localhost:8000/admin${NC}"
    
    echo -e "\n${CYAN}🔧 Available commands:${NC}"
    echo -e "${NC}- make dev          Start development servers${NC}"
    echo -e "${NC}- make test         Run all tests${NC}"
    echo -e "${NC}- make build        Build applications${NC}"
    echo -e "${NC}- make lint         Run code linting${NC}"
    echo -e "${NC}- make format       Format code${NC}"
    echo -e "${NC}- make docker-up    Start with Docker${NC}"
    
else
    echo -e "\n${YELLOW}⚠️ Setup completed with some issues. Please review the errors above.${NC}"
fi

echo -e "\n${CYAN}📚 Documentation:${NC}"
echo -e "${NC}- Development guide: docs/development.md${NC}"
echo -e "${NC}- API documentation: http://localhost:8000/docs${NC}"
echo -e "${NC}- Component library: http://localhost:6006 (Storybook)${NC}"