#!/bin/bash

# BW-MetaBase Quick Server Deployment Script for 83.229.35.162
# This is a simplified version that handles permission issues better

set -e

echo "🚀 BW-MetaBase Server Deployment - Phase 1 (Fixed)"
echo "Server: 83.229.35.162"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we have sudo access
check_permissions() {
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo access. Please run with:"
        print_error "sudo ./deploy-server-fixed.sh"
        print_error "Or ensure your user has sudo privileges"
        exit 1
    fi
    print_status "Sudo access confirmed ✓"
}

# Install Docker Compose using pip (more reliable)
install_docker_compose_pip() {
    if ! command -v docker-compose &> /dev/null; then
        print_step "Installing Docker Compose via pip..."
        
        # Install python3-pip if not present
        if ! command -v pip3 &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3-pip
        fi
        
        # Install docker-compose via pip
        sudo pip3 install docker-compose
        
        print_status "Docker Compose installed successfully ✓"
    else
        print_status "Docker Compose already installed ✓"
    fi
}

# Alternative Docker Compose installation
install_docker_compose_alt() {
    if ! command -v docker-compose &> /dev/null; then
        print_step "Installing Docker Compose (alternative method)..."
        
        # Try the curl method with proper permissions
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
        
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        # Create symlink if needed
        if [ ! -f /usr/bin/docker-compose ]; then
            sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
        fi
        
        print_status "Docker Compose installed successfully ✓"
    else
        print_status "Docker Compose already installed ✓"
    fi
}

# Quick Docker installation using the convenience script
install_docker_quick() {
    if ! command -v docker &> /dev/null; then
        print_step "Installing Docker..."
        
        # Download and run Docker installation script
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        # Start and enable Docker
        sudo systemctl start docker
        sudo systemctl enable docker
        
        print_status "Docker installed successfully ✓"
        rm get-docker.sh
    else
        print_status "Docker already installed ✓"
    fi
}

# Simple firewall setup
setup_firewall_simple() {
    print_step "Configuring basic firewall..."
    
    if command -v ufw &> /dev/null; then
        # Allow necessary ports
        sudo ufw allow 22/tcp comment 'SSH'
        sudo ufw allow 80/tcp comment 'HTTP'
        sudo ufw allow 443/tcp comment 'HTTPS'
        
        # Enable if not already enabled
        if ! sudo ufw status | grep -q "Status: active"; then
            sudo ufw --force enable
        fi
        
        print_status "Firewall configured ✓"
        sudo ufw status numbered
    else
        print_warning "UFW not available, skipping firewall configuration"
    fi
}

# Setup environment with error handling
setup_environment() {
    print_step "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status ".env created from template"
        else
            print_error ".env.example not found! Are you in the correct directory?"
            exit 1
        fi
    fi
    
    # Generate secure passwords only if they don't exist
    if grep -q "your_secure.*password" .env 2>/dev/null; then
        print_step "Generating secure passwords..."
        
        # Use openssl to generate secure passwords
        POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        MB_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-32)
        JWT_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        
        # Update .env file
        sed -i.bak "s/your_secure_postgres_password_here/$POSTGRES_PASS/g" .env
        sed -i.bak "s/your_secure_redis_password_here/$REDIS_PASS/g" .env
        sed -i.bak "s/your_very_secure_metabase_encryption_key_here_32_chars_minimum/$MB_SECRET/g" .env
        sed -i.bak "s/your_jwt_secret_key_here/$JWT_SECRET/g" .env
        sed -i.bak "s/your_encryption_key_here/$ENCRYPTION_KEY/g" .env
        
        print_status "Secure passwords generated ✓"
    else
        print_status "Environment already configured ✓"
    fi
}

# Start services with better error handling
start_services() {
    print_step "Starting BW-MetaBase services..."
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found! Are you in the correct directory?"
        exit 1
    fi
    
    # Pull images first
    print_status "Pulling Docker images..."
    docker-compose pull
    
    # Build nginx with custom configuration
    print_status "Building nginx container..."
    docker-compose build nginx
    
    # Start all services
    print_status "Starting all services..."
    docker-compose up -d
    
    print_status "Services started ✓"
}

# Wait for services with timeout
wait_for_services() {
    print_step "Waiting for services to start..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local running_count=$(docker-compose ps --filter "status=running" | grep -c "Up" || echo "0")
        
        if [ "$running_count" -ge 3 ]; then  # At least 3 services should be running
            print_status "Services are starting up ✓"
            break
        fi
        
        sleep 5
        attempt=$((attempt + 1))
        print_status "Waiting for services... ($attempt/$max_attempts)"
    done
    
    # Show final status
    docker-compose ps
}

# Display completion info
show_completion() {
    echo ""
    echo "🎉 BW-MetaBase Deployment Complete!"
    echo "=================================="
    echo ""
    echo "Service Status:"
    docker-compose ps
    echo ""
    echo "Access Information:"
    echo "  • Metabase (local): http://localhost:3000"
    echo "  • Metabase (public): http://$(curl -s ifconfig.me):3000"
    echo "  • Once DNS is configured: https://StoreMgnt.Beachwood.me"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure DNS: StoreMgnt.Beachwood.me → $(curl -s ifconfig.me)"
    echo "  2. Access Metabase to complete setup"
    echo "  3. Configure SSL certificates (will happen automatically)"
    echo ""
    echo "Useful Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Restart: docker-compose restart"
    echo "  • Stop: docker-compose down"
    echo ""
}

# Main execution with error handling
main() {
    print_step "Starting deployment..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found!"
        print_error "Please run this script from the BW-MetaBase directory"
        print_error "cd BW-MetaBase && ./deploy-server-fixed.sh"
        exit 1
    fi
    
    check_permissions
    install_docker_quick
    
    # Try pip installation first, fall back to curl method
    if ! install_docker_compose_pip; then
        print_warning "Pip installation failed, trying alternative method..."
        install_docker_compose_alt
    fi
    
    setup_firewall_simple
    setup_environment
    start_services
    wait_for_services
    show_completion
    
    print_status "Deployment completed successfully! 🚀"
}

# Handle interruption
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 1' INT

# Run with error handling
if ! main "$@"; then
    print_error "Deployment failed. Check the logs above for details."
    print_error "You can try running individual commands manually or check the documentation."
    exit 1
fi
