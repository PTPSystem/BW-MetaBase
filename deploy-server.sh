#!/bin/bash

# BW-MetaBase Server Deployment Script for 83.229.35.162
# This script sets up Phase 1 on the production server

set -e

echo "🚀 BW-MetaBase Server Deployment - Phase 1"
echo "Server: 83.229.35.162"
echo "======================================="

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

# Check if running as root
check_user() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Consider creating a dedicated user for deployment."
    fi
    print_status "User check completed ✓"
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        print_step "Installing Docker..."
        
        # Update package index
        apt-get update
        
        # Install prerequisites
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Set up stable repository
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker Engine
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io
        
        # Start and enable Docker
        systemctl start docker
        systemctl enable docker
        
        print_status "Docker installed successfully ✓"
    else
        print_status "Docker already installed ✓"
    fi
}

# Install Docker Compose if not present
install_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_step "Installing Docker Compose..."
        
        # Download latest version
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        
        # Make executable
        chmod +x /usr/local/bin/docker-compose
        
        # Create symlink
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        
        print_status "Docker Compose installed successfully ✓"
    else
        print_status "Docker Compose already installed ✓"
    fi
}

# Configure firewall
setup_firewall() {
    print_step "Configuring firewall..."
    
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Reset firewall to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (important - don't lock yourself out!)
    ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_status "Firewall configured ✓"
    ufw status
}

# Setup production environment
setup_production_env() {
    print_step "Setting up production environment..."
    
    # Copy .env.example to .env if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_status ".env file created from template"
    fi
    
    # Generate secure passwords
    print_status "Generating secure production passwords..."
    
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    MB_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-32)
    JWT_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update .env with production values
    sed -i "s/your_secure_postgres_password_here/$POSTGRES_PASS/g" .env
    sed -i "s/your_secure_redis_password_here/$REDIS_PASS/g" .env
    sed -i "s/your_very_secure_metabase_encryption_key_here_32_chars_minimum/$MB_SECRET/g" .env
    sed -i "s/your_jwt_secret_key_here/$JWT_SECRET/g" .env
    sed -i "s/your_encryption_key_here/$ENCRYPTION_KEY/g" .env
    
    # Set production settings
    sed -i "s/CERTBOT_STAGING=false/CERTBOT_STAGING=false/g" .env
    sed -i "s|MB_SITE_URL=https://StoreMgnt.Beachwood.me|MB_SITE_URL=https://StoreMgnt.Beachwood.me|g" .env
    
    print_status "Production environment configured ✓"
}

# Create necessary directories
create_directories() {
    print_step "Creating application directories..."
    
    # Create directory structure
    mkdir -p /opt/bw-metabase
    mkdir -p /opt/bw-metabase/data/{postgres,redis,metabase}
    mkdir -p /opt/bw-metabase/logs
    mkdir -p /opt/bw-metabase/backups
    mkdir -p /var/log/bw-metabase
    
    # Set proper permissions
    chown -R $USER:$USER /opt/bw-metabase
    chmod -R 755 /opt/bw-metabase
    
    print_status "Directories created ✓"
}

# Pull Docker images
pull_images() {
    print_step "Pulling Docker images..."
    
    docker pull postgres:15-alpine
    docker pull redis:7-alpine
    docker pull metabase/metabase:latest
    docker pull nginx:alpine
    
    print_status "Docker images pulled ✓"
}

# Start services
start_services() {
    print_step "Starting BW-MetaBase services..."
    
    # Build and start services
    docker-compose build nginx
    docker-compose up -d
    
    print_status "Services started ✓"
}

# Wait for services to be healthy
wait_for_health() {
    print_step "Waiting for services to become healthy..."
    
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        healthy_count=$(docker-compose ps --filter "status=running" | grep -c "Up (healthy)" || echo "0")
        total_services=4  # postgres, redis, metabase, nginx
        
        if [ "$healthy_count" -eq "$total_services" ]; then
            print_status "All services are healthy ✓"
            return 0
        fi
        
        sleep 10
        attempt=$((attempt + 1))
        print_status "Waiting for services... ($attempt/$max_attempts) - $healthy_count/$total_services healthy"
    done
    
    print_warning "Some services may not be fully healthy yet."
    docker-compose ps
}

# Setup SSL certificates
setup_ssl() {
    print_step "Setting up SSL certificates..."
    
    # Wait a bit for nginx to fully start
    sleep 30
    
    # Check if certificates already exist
    if docker-compose exec nginx ls /etc/letsencrypt/live/StoreMgnt.Beachwood.me/fullchain.pem &>/dev/null; then
        print_status "SSL certificates already exist ✓"
    else
        print_status "Attempting to obtain SSL certificates..."
        
        # Try to obtain certificates
        docker-compose exec nginx certbot certonly \
            --webroot --webroot-path=/var/www/certbot \
            --email admin@beachwood.me --agree-tos --no-eff-email \
            -d StoreMgnt.Beachwood.me || {
            print_warning "Automatic SSL certificate generation failed."
            print_warning "You may need to:"
            print_warning "1. Ensure DNS is properly configured"
            print_warning "2. Check that ports 80 and 443 are accessible"
            print_warning "3. Manually run: docker-compose exec nginx certbot certonly --webroot --webroot-path=/var/www/certbot --email admin@beachwood.me --agree-tos --no-eff-email -d StoreMgnt.Beachwood.me"
        }
        
        # Reload nginx
        docker-compose exec nginx nginx -s reload
    fi
}

# Setup backup cron job
setup_backups() {
    print_step "Setting up automated backups..."
    
    # Create backup script
    cat > /opt/bw-metabase/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/bw-metabase/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup databases
docker-compose exec -T postgres pg_dump -U metabase metabase > $BACKUP_DIR/metabase_$DATE.sql
docker-compose exec -T postgres pg_dump -U metabase bw_sample_data > $BACKUP_DIR/sample_data_$DATE.sql

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz docker/ config/ .env docker-compose.yml

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

    chmod +x /opt/bw-metabase/backup.sh
    
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/bw-metabase/backup.sh >> /var/log/bw-metabase/backup.log 2>&1") | crontab -
    
    print_status "Backup cron job configured ✓"
}

# Display final information
show_completion_info() {
    echo ""
    echo "🎉 BW-MetaBase Phase 1 Deployment Complete!"
    echo "========================================="
    echo ""
    echo "Server Information:"
    echo "  • Server IP: 83.229.35.162"
    echo "  • Metabase URL: https://StoreMgnt.Beachwood.me"
    echo "  • Local access: http://83.229.35.162:3000"
    echo ""
    echo "Service Status:"
    docker-compose ps
    echo ""
    echo "Next Steps:"
    echo "  1. Configure DNS for StoreMgnt.Beachwood.me → 83.229.35.162"
    echo "  2. Access Metabase to complete initial setup"
    echo "  3. Configure sample database connection in Metabase"
    echo "  4. Set up user accounts and permissions"
    echo ""
    echo "Useful Commands:"
    echo "  • Check services: docker-compose ps"
    echo "  • View logs: docker-compose logs -f [service]"
    echo "  • Restart services: docker-compose restart"
    echo "  • Manual backup: /opt/bw-metabase/backup.sh"
    echo ""
    echo "Support:"
    echo "  • Logs location: /var/log/bw-metabase/"
    echo "  • Backups location: /opt/bw-metabase/backups/"
    echo "  • Configuration: /opt/bw-metabase/"
    echo ""
    
    print_status "Phase 1 deployment completed successfully! 🚀"
}

# Main execution
main() {
    print_step "Starting BW-MetaBase server deployment..."
    
    check_user
    install_docker
    install_docker_compose
    setup_firewall
    setup_production_env
    create_directories
    pull_images
    start_services
    wait_for_health
    setup_ssl
    setup_backups
    show_completion_info
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 1' INT

# Check if running on correct server
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "unknown")
if [ "$SERVER_IP" != "83.229.35.162" ]; then
    print_warning "This script is designed for server 83.229.35.162"
    print_warning "Current server IP: $SERVER_IP"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Run main function
main "$@"
