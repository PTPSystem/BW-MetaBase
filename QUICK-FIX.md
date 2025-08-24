# Manual Deployment Guide - Quick Fix for 83.229.35.162

## Issue Resolution

The deployment script failed due to permission issues when installing Docker Compose. Here's how to fix it:

### Option 1: Use the Fixed Script (Recommended)

```bash
# Use the new fixed deployment script
sudo ./deploy-server-fixed.sh
```

### Option 2: Manual Installation Steps

If the automated script still has issues, follow these manual steps:

#### 1. Install Docker Compose Manually

```bash
# Method A: Using pip (recommended)
sudo apt update
sudo apt install -y python3-pip
sudo pip3 install docker-compose

# Method B: Direct download (if pip fails)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

#### 2. Verify Installation

```bash
docker-compose --version
```

#### 3. Continue with Deployment

```bash
# Setup environment
cp .env.example .env

# Generate secure passwords
nano .env  # Edit the passwords manually or use the script

# Start services
docker-compose pull
docker-compose build nginx
docker-compose up -d
```

### Option 3: Quick Manual Fix

If you just need to continue from where it failed:

```bash
# Install Docker Compose using pip
sudo apt update
sudo apt install -y python3-pip
sudo pip3 install docker-compose

# Verify it works
docker-compose --version

# Continue with the original script or run manually:
./deploy-server.sh
```

## Current Status Check

After fixing Docker Compose installation, check your services:

```bash
# Check what's running
docker ps

# Check compose services
docker-compose ps

# If nothing is running, start everything:
docker-compose up -d
```

## Quick Recovery Commands

If you need to start fresh:

```bash
# Stop everything
docker-compose down

# Remove any partial containers
docker system prune -f

# Start fresh
docker-compose up -d
```

## Testing Access

Once everything is running:

```bash
# Check services
docker-compose ps

# Test Metabase access
curl -I http://localhost:3000

# Check logs if there are issues
docker-compose logs -f metabase
```

## Next Steps

1. **Verify all containers are running**:
   ```bash
   docker-compose ps
   ```

2. **Access Metabase**: 
   - Local: http://83.229.35.162:3000
   - Setup admin account and connect to sample database

3. **Configure DNS**: Point StoreMgnt.Beachwood.me to 83.229.35.162

4. **SSL will auto-configure** once DNS is working

## Troubleshooting

If you still have issues:

1. **Check Docker daemon**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

2. **Check user permissions**:
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Check ports**:
   ```bash
   netstat -tulpn | grep -E "(80|443|3000|5432)"
   ```

The fixed script (`deploy-server-fixed.sh`) should resolve the permission issues you encountered.
