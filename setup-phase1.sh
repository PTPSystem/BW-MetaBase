#!/bin/bash

# BW-MetaBase Development Setup Script
# This script sets up the development environment for Phase 1

set -e

echo "🚀 Setting up BW-MetaBase Development Environment - Phase 1"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed ✓"
}

# Check if .env file exists
setup_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration values!"
        print_warning "Especially update passwords and secret keys!"
    else
        print_status ".env file exists ✓"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create logs directory for nginx
    mkdir -p docker/nginx/logs
    
    # Create plugins directory for metabase
    mkdir -p docker/metabase/plugins
    
    # Create ssl directory
    mkdir -p config/ssl
    
    # Create data directories (will be used by Docker volumes)
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/metabase
    
    print_status "Directories created ✓"
}

# Generate secure passwords if needed
generate_passwords() {
    if [ -f ".env" ] && grep -q "your_secure.*password" .env; then
        print_warning "Generating secure passwords..."
        
        # Generate random passwords
        POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        MB_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-32)
        JWT_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        
        # Update .env file
        sed -i.bak "s/your_secure_postgres_password_here/$POSTGRES_PASS/g" .env
        sed -i.bak "s/your_secure_redis_password_here/$REDIS_PASS/g" .env
        sed -i.bak "s/your_very_secure_metabase_encryption_key_here_32_chars_minimum/$MB_SECRET/g" .env
        sed -i.bak "s/your_jwt_secret_key_here/$JWT_SECRET/g" .env
        
        print_status "Secure passwords generated and updated in .env ✓"
        print_warning "Backup created as .env.bak"
    fi
}

# Validate environment
validate_env() {
    print_status "Validating environment configuration..."
    
    # Source the .env file
    set -a
    source .env
    set +a
    
    # Check required variables
    required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "MB_ENCRYPTION_SECRET_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        print_error "Please update your .env file"
        exit 1
    fi
    
    print_status "Environment validation passed ✓"
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build nginx with custom configuration
    docker-compose build nginx
    
    # Start all services
    docker-compose up -d
    
    print_status "Services started ✓"
}

# Check service health
check_health() {
    print_status "Checking service health..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            print_status "All services are healthy ✓"
            return 0
        fi
        
        sleep 10
        attempt=$((attempt + 1))
        print_status "Waiting for services to become healthy... (attempt $attempt/$max_attempts)"
    done
    
    print_warning "Some services may not be fully healthy yet. Check with 'docker-compose ps'"
}

# Display access information
show_access_info() {
    echo ""
    echo "🎉 Phase 1 Setup Complete!"
    echo "========================="
    echo ""
    echo "Services Status:"
    docker-compose ps
    echo ""
    echo "Access Information:"
    echo "  • Metabase (local): http://localhost:3000"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo ""
    echo "Production URLs (when SSL is configured):"
    echo "  • Metabase: https://StoreMgnt.Beachwood.me"
    echo "  • Existing site: https://str.ptpsystem.com"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure your domain DNS to point to $SERVER_IP"
    echo "  2. Update .env with production values"
    echo "  3. Run 'docker-compose down && docker-compose up -d' to restart with new config"
    echo "  4. Access Metabase at http://localhost:3000 to complete initial setup"
    echo ""
    echo "Useful Commands:"
    echo "  • View logs: docker-compose logs -f [service_name]"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • View service status: docker-compose ps"
}

# Main execution
main() {
    echo "Starting Phase 1 setup..."
    
    check_docker
    setup_env
    create_directories
    generate_passwords
    validate_env
    start_services
    check_health
    show_access_info
    
    print_status "Phase 1 setup completed successfully! 🚀"
}

# Handle script interruption
trap 'echo -e "\n${RED}Setup interrupted${NC}"; exit 1' INT

# Run main function
main "$@"
