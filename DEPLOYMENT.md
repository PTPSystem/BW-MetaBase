# Phase 1 Production Deployment Guide

## Server: 83.229.35.162

### Prerequisites

1. **DNS Configuration**
   ```bash
   # Configure A records to point to your server
   StoreMgnt.Beachwood.me -> 83.229.35.162
   str.ptpsystem.com -> 83.229.35.162
   ```

2. **Server Requirements**
   - Docker and Docker Compose installed
   - Ports 80 and 443 available
   - At least 4GB RAM recommended
   - 20GB+ disk space

### Deployment Steps

1. **Clone and Setup**
   ```bash
   git clone https://github.com/PTPSystem/BW-MetaBase.git
   cd BW-MetaBase
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

3. **Important .env Updates for Production**
   ```env
   # Set to production domain
   MB_SITE_URL=https://StoreMgnt.Beachwood.me
   
   # Use strong, unique passwords
   POSTGRES_PASSWORD=your_very_secure_production_password
   REDIS_PASSWORD=your_very_secure_redis_password
   MB_ENCRYPTION_SECRET_KEY=your_32_char_minimum_encryption_key
   
   # Set to false for production certificates
   CERTBOT_STAGING=false
   
   # Production email for SSL certificates
   SSL_EMAIL=admin@beachwood.me
   ```

4. **Run Setup Script**
   ```bash
   chmod +x setup-phase1.sh
   ./setup-phase1.sh
   ```

5. **Verify Services**
   ```bash
   docker-compose ps
   docker-compose logs -f nginx
   docker-compose logs -f metabase
   ```

### SSL Certificate Setup

The nginx container will automatically attempt to obtain SSL certificates using Let's Encrypt. Monitor the logs:

```bash
docker-compose logs -f nginx
```

If automatic certificate generation fails, you can manually obtain certificates:

```bash
# Access the nginx container
docker-compose exec nginx sh

# Manually run certbot
certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email admin@beachwood.me --agree-tos --no-eff-email \
  -d StoreMgnt.Beachwood.me

certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email admin@beachwood.me --agree-tos --no-eff-email \
  -d str.ptpsystem.com

# Reload nginx
nginx -s reload
```

### Initial Metabase Setup

1. **Access Metabase**
   - Local: http://localhost:3000
   - Production: https://StoreMgnt.Beachwood.me

2. **Initial Configuration**
   - Create admin user
   - Connect to sample database (already configured)
   - Configure authentication settings

3. **Database Connection for Sample Data**
   ```
   Database Type: PostgreSQL
   Host: postgres
   Port: 5432
   Database Name: bw_sample_data
   Username: metabase
   Password: [from your .env POSTGRES_PASSWORD]
   ```

### Monitoring and Maintenance

1. **Health Checks**
   ```bash
   # Check all services
   docker-compose ps
   
   # Check specific service health
   curl -f http://localhost:3000/api/health
   
   # Check nginx status
   curl -I https://StoreMgnt.Beachwood.me
   ```

2. **Log Monitoring**
   ```bash
   # All logs
   docker-compose logs -f
   
   # Specific service logs
   docker-compose logs -f metabase
   docker-compose logs -f nginx
   docker-compose logs -f postgres
   ```

3. **Certificate Renewal**
   Certificates will auto-renew via cron job in nginx container. Check renewal:
   ```bash
   docker-compose exec nginx certbot renew --dry-run
   ```

### Backup Strategy

1. **Database Backup**
   ```bash
   # Create backup
   docker-compose exec postgres pg_dump -U metabase metabase > metabase_backup.sql
   docker-compose exec postgres pg_dump -U metabase bw_sample_data > sample_data_backup.sql
   
   # Restore backup
   docker-compose exec -T postgres psql -U metabase metabase < metabase_backup.sql
   ```

2. **Configuration Backup**
   ```bash
   # Backup entire configuration
   tar -czf bw-metabase-config-$(date +%Y%m%d).tar.gz \
     docker/ config/ .env docker-compose.yml
   ```

### Troubleshooting

1. **Service Won't Start**
   ```bash
   # Check logs for errors
   docker-compose logs service_name
   
   # Restart specific service
   docker-compose restart service_name
   
   # Rebuild if needed
   docker-compose build --no-cache service_name
   ```

2. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   docker-compose exec nginx certbot certificates
   
   # Force renewal
   docker-compose exec nginx certbot renew --force-renewal
   
   # Use staging for testing
   # Set CERTBOT_STAGING=true in .env and restart
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker-compose exec metabase nc -z postgres 5432
   
   # Check database logs
   docker-compose logs postgres
   
   # Access database directly
   docker-compose exec postgres psql -U metabase -d metabase
   ```

4. **Memory Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Adjust memory limits in docker-compose.yml if needed
   # For metabase, update JAVA_OPTS: "-Xmx4g" for 4GB
   ```

### Performance Optimization

1. **Database Tuning**
   Add to docker-compose.yml postgres service:
   ```yaml
   command: >
     postgres
     -c shared_preload_libraries=pg_stat_statements
     -c max_connections=200
     -c shared_buffers=256MB
     -c effective_cache_size=1GB
   ```

2. **Nginx Caching**
   Already configured in nginx.conf for static assets

3. **Metabase Performance**
   - Increase Java heap size via JAVA_OPTS
   - Configure Redis for caching
   - Enable Metabase caching in admin settings

### Security Considerations

1. **Firewall Rules**
   ```bash
   # Only allow necessary ports
   ufw allow 22    # SSH
   ufw allow 80    # HTTP
   ufw allow 443   # HTTPS
   ufw enable
   ```

2. **Regular Updates**
   ```bash
   # Update containers monthly
   docker-compose pull
   docker-compose down
   docker-compose up -d
   ```

3. **Access Logs**
   Monitor nginx access logs for suspicious activity:
   ```bash
   docker-compose exec nginx tail -f /var/log/nginx/access.log
   ```

### Scaling Considerations

For future scaling, consider:
- Moving to Docker Swarm or Kubernetes
- External PostgreSQL database (RDS, etc.)
- Load balancer for multiple Metabase instances
- CDN for static assets
- Separate Redis cluster

---

**Note**: This guide covers Phase 1 deployment. Future phases will add ETL pipelines, user authentication, and advanced features.
