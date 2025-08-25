#!/bin/bash
#
# Daily BI Import Cron Script
# Runs the ETL container to import BI Dimensions and BI At Scale Import files
# Schedule: Daily at 6:00 AM
# Add to crontab: 0 6 * * * /path/to/this/script/daily_bi_import.sh

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Set up logging
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_bi_import_$(date +%Y%m%d_%H%M%S).log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Daily BI Import Process"
log "📁 Project Directory: $PROJECT_DIR"
log "📝 Log File: $LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || {
    log "❌ Failed to change to project directory: $PROJECT_DIR"
    exit 1
}

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    log "❌ docker-compose.yml not found in $PROJECT_DIR"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    log "📋 Loading environment variables from .env"
    source .env
else
    log "⚠️ No .env file found - using defaults"
fi

# Check required environment variables
required_vars=("AZURE_TENANT_ID" "AZURE_CLIENT_ID" "AZURE_CLIENT_SECRET" "POSTGRES_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    log "❌ Missing required environment variables: ${missing_vars[*]}"
    exit 1
fi

log "✅ Environment variables validated"

# Remove any existing ETL container
log "🧹 Cleaning up any existing ETL container"
docker-compose rm -f etl 2>/dev/null || true

# Rebuild ETL container to ensure latest code
log "🔨 Rebuilding ETL container"
if docker-compose build etl >> "$LOG_FILE" 2>&1; then
    log "✅ ETL container rebuilt successfully"
else
    log "❌ Failed to rebuild ETL container"
    exit 1
fi

# Run the ETL import
log "📊 Starting BI data import"
if docker-compose run --rm etl >> "$LOG_FILE" 2>&1; then
    log "✅ BI import completed successfully"
    
    # Clean up container
    docker-compose rm -f etl 2>/dev/null || true
    
    # Log import summary
    log "📈 Import Summary:"
    log "   - BI Dimensions.xlsx imported to bi_dimensions table"
    log "   - BI At Scale Import.xlsx imported to bi_at_scale_import table"
    
else
    log "❌ BI import failed"
    
    # Clean up container even on failure
    docker-compose rm -f etl 2>/dev/null || true
    
    # Show last few lines of container logs for debugging
    log "🔍 Container logs (last 20 lines):"
    docker-compose logs --tail=20 etl >> "$LOG_FILE" 2>&1 || true
    
    exit 1
fi

# Keep only last 30 days of logs
log "🧹 Cleaning up old log files"
find "$LOG_DIR" -name "daily_bi_import_*.log" -mtime +30 -delete 2>/dev/null || true

log "🎉 Daily BI Import Process Completed Successfully"
log "📊 Check Metabase for updated data in tables: bi_dimensions, bi_at_scale_import"

# Optional: Send notification (uncomment if needed)
# echo "Daily BI Import completed successfully at $(date)" | mail -s "BW-MetaBase: Daily Import Success" admin@beachwood.me
