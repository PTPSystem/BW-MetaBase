# Server Deployment Instructions for 83.229.35.162

## Prerequisites

Before deploying to the server, ensure:

1. **DNS Configuration**
   ```
   StoreMgnt.Beachwood.me → 83.229.35.162
   str.ptpsystem.com → 83.229.35.162
   ```

2. **Server Access**
   - SSH access to 83.229.35.162
   - Root or sudo privileges
   - Ubuntu/Debian-based server

## Quick Deployment

### Step 1: Connect to Server
```bash
ssh root@83.229.35.162
# or
ssh your_user@83.229.35.162
```

### Step 2: Clone Repository
```bash
# Install git if needed
apt update && apt install -y git

# Clone the repository
git clone https://github.com/PTPSystem/BW-MetaBase.git
cd BW-MetaBase
```

### Step 3: Run Deployment Script
```bash
# Make script executable
chmod +x deploy-server.sh

# Run deployment (as root or with sudo)
sudo ./deploy-server.sh
```

The script will automatically:
- ✅ Install Docker and Docker Compose
- ✅ Configure firewall (ports 22, 80, 443)
- ✅ Generate secure passwords
- ✅ Create production environment
- ✅ Pull and start all containers
- ✅ Attempt SSL certificate setup
- ✅ Configure automated backups

### Step 4: Verify Deployment
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f metabase

# Test local access
curl -I http://localhost:3000
```

## Manual Deployment (Alternative)

If you prefer manual control:

### 1. Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit with production values
nano .env
```

### 3. Start Services
```bash
# Pull images
docker-compose pull

# Build and start
docker-compose up -d

# Check status
docker-compose ps
```

## Post-Deployment Configuration

### 1. Metabase Initial Setup

Access Metabase at: `http://83.229.35.162:3000` (or `https://StoreMgnt.Beachwood.me` if SSL is working)

1. **Create Admin Account**
   - Email: admin@beachwood.me
   - Password: [choose secure password]
   - Name: System Administrator

2. **Connect to Sample Database**
   ```
   Database Type: PostgreSQL
   Host: postgres
   Port: 5432
   Database: bw_sample_data
   Username: metabase
   Password: [from .env POSTGRES_PASSWORD]
   ```

3. **Configure Authentication**
   - Go to Admin → Settings → Authentication
   - Configure as needed for your organization

### 2. SSL Certificate Troubleshooting

If SSL certificates didn't generate automatically:

```bash
# Check nginx logs
docker-compose logs nginx

# Manual certificate generation
docker-compose exec nginx certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email admin@beachwood.me --agree-tos --no-eff-email \
  -d StoreMgnt.Beachwood.me

# Reload nginx
docker-compose exec nginx nginx -s reload
```

### 3. Firewall Verification
```bash
# Check firewall status
ufw status

# Should show:
# 22/tcp     ALLOW       Anywhere
# 80/tcp     ALLOW       Anywhere
# 443/tcp    ALLOW       Anywhere
```

## Monitoring and Maintenance

### Service Health Checks
```bash
# Check all services
docker-compose ps

# Check individual service logs
docker-compose logs -f metabase
docker-compose logs -f nginx
docker-compose logs -f postgres

# Test endpoints
curl -f http://localhost:3000/api/health
```

### Backup Verification
```bash
# Check backup location
ls -la /opt/bw-metabase/backups/

# Manual backup
/opt/bw-metabase/backup.sh

# Check backup logs
tail -f /var/log/bw-metabase/backup.log
```

### Resource Monitoring
```bash
# Check container resources
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using ports 80/443
   netstat -tulpn | grep :80
   netstat -tulpn | grep :443
   
   # Stop conflicting services
   systemctl stop apache2  # if Apache is running
   systemctl stop nginx    # if system nginx is running
   ```

2. **SSL Certificate Issues**
   ```bash
   # Use staging certificates for testing
   # In .env, set: CERTBOT_STAGING=true
   
   # Force certificate renewal
   docker-compose exec nginx certbot renew --force-renewal
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker-compose exec metabase nc -z postgres 5432
   
   # Check database logs
   docker-compose logs postgres
   
   # Reset database
   docker-compose down
   docker volume rm bw-postgres-data
   docker-compose up -d
   ```

4. **Memory Issues**
   ```bash
   # Check available memory
   free -h
   
   # Reduce Metabase memory usage in docker-compose.yml
   # Change JAVA_OPTS: "-Xmx1g" for servers with limited RAM
   ```

### Recovery Procedures

1. **Complete Service Restart**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Database Recovery**
   ```bash
   # Restore from backup
   docker-compose exec -T postgres psql -U metabase metabase < backup.sql
   ```

3. **Certificate Recovery**
   ```bash
   # Regenerate self-signed certificates
   docker-compose exec nginx openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /etc/ssl/certs/StoreMgnt.Beachwood.me/privkey.pem \
     -out /etc/ssl/certs/StoreMgnt.Beachwood.me/fullchain.pem \
     -subj "/CN=StoreMgnt.Beachwood.me"
   ```

## Security Considerations

1. **Regular Updates**
   ```bash
   # Update monthly
   docker-compose pull
   docker-compose down
   docker-compose up -d
   ```

2. **Monitor Access Logs**
   ```bash
   docker-compose exec nginx tail -f /var/log/nginx/access.log
   ```

3. **Backup Security**
   - Backups are stored locally in `/opt/bw-metabase/backups/`
   - Consider encrypting sensitive backups
   - Set up off-site backup for production

## Next Steps After Phase 1

Once Phase 1 is deployed and working:

1. **User Management**: Set up initial users and store relationships
2. **Dashboard Creation**: Build initial dashboards with sample data
3. **Phase 2 Planning**: ETL pipeline development
4. **Monitoring Setup**: Enhanced logging and alerting
5. **Performance Tuning**: Optimize for production workload

---

**Support**: For issues during deployment, check logs first:
```bash
docker-compose logs -f
```
