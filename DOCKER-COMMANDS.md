# BW-MetaBase Docker Commands Reference

## Quick Start Commands

```bash
# Setup Phase 1 (run once)
./setup-phase1.sh

# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# View service status
docker-compose ps
```

## Individual Service Management

```bash
# Start specific service
docker-compose up -d metabase

# Stop specific service
docker-compose stop metabase

# Restart specific service
docker-compose restart metabase

# Rebuild specific service
docker-compose build --no-cache metabase
docker-compose up -d metabase
```

## Logs and Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f metabase
docker-compose logs -f nginx
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 metabase

# Monitor resource usage
docker stats
```

## Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U metabase -d metabase

# Connect to sample data database
docker-compose exec postgres psql -U metabase -d bw_sample_data

# Create database backup
docker-compose exec postgres pg_dump -U metabase metabase > backup.sql

# Restore database backup
docker-compose exec -T postgres psql -U metabase metabase < backup.sql

# Reset sample data
docker-compose exec postgres psql -U metabase -d bw_sample_data -f /docker-entrypoint-initdb.d/01-sample-data.sql
```

## SSL and Nginx Operations

```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx configuration
docker-compose exec nginx nginx -s reload

# Check SSL certificates
docker-compose exec nginx certbot certificates

# Renew SSL certificates (dry run)
docker-compose exec nginx certbot renew --dry-run

# Force certificate renewal
docker-compose exec nginx certbot renew --force-renewal

# Generate new certificate manually
docker-compose exec nginx certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@beachwood.me \
  --agree-tos --no-eff-email \
  -d StoreMgnt.Beachwood.me
```

## Troubleshooting Commands

```bash
# Check service health
curl -f http://localhost:3000/api/health

# Test database connection
docker-compose exec metabase nc -z postgres 5432

# Test Redis connection
docker-compose exec redis redis-cli ping

# View container details
docker inspect bw-metabase

# Access container shell
docker-compose exec metabase bash
docker-compose exec nginx sh
docker-compose exec postgres sh

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## Backup and Restore

```bash
# Complete backup
tar -czf bw-metabase-backup-$(date +%Y%m%d).tar.gz \
  docker/ config/ .env docker-compose.yml

# Database backup
docker-compose exec postgres pg_dumpall -U metabase > full_backup.sql

# Volume backup
docker run --rm -v bw-postgres-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres-data-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v bw-postgres-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/postgres-data-backup.tar.gz -C /data
```

## Development Commands

```bash
# Watch logs during development
docker-compose logs -f | grep -E "(metabase|nginx|postgres)"

# Update all images
docker-compose pull

# Rebuild everything from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Reset entire environment (WARNING: deletes all data)
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

## Network and Port Information

```bash
# Default ports:
# - Metabase: 3000 (internal), 443 (external via nginx)
# - PostgreSQL: 5432
# - Redis: 6379
# - Nginx: 80, 443

# Check port usage
netstat -tulpn | grep -E "(3000|5432|6379|80|443)"

# Test connectivity
telnet localhost 3000
telnet localhost 5432
```

## Performance Monitoring

```bash
# Monitor container resources
docker stats --no-stream

# Check Metabase JVM memory
docker-compose exec metabase jps -v

# Monitor database connections
docker-compose exec postgres psql -U metabase -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check disk space
df -h
docker system df
```

## Useful Aliases

Add these to your `.bashrc` or `.zshrc`:

```bash
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dcps='docker-compose ps'
alias dclogs='docker-compose logs -f'
alias dcrestart='docker-compose restart'

# Specific to BW-MetaBase
alias mb-logs='docker-compose logs -f metabase'
alias mb-restart='docker-compose restart metabase'
alias mb-db='docker-compose exec postgres psql -U metabase -d bw_sample_data'
```
