#!/bin/bash
#
# Deploy Daily BI Import to Production Server
# This script updates the production server with the new ETL functionality
#

set -e  # Exit on any error

# Configuration
SERVER_IP="83.229.35.162"
SERVER_USER="howardshen"
PROJECT_PATH="/home/howardshen/BW-MetaBase"

echo "🚀 Deploying Daily BI Import to Production Server"
echo "📡 Server: $SERVER_USER@$SERVER_IP"
echo "📁 Path: $PROJECT_PATH"
echo

# Function to run command on server
run_remote() {
    ssh "$SERVER_USER@$SERVER_IP" "$1"
}

# Function to copy file to server
copy_to_server() {
    local local_file="$1"
    local remote_file="$2"
    scp "$local_file" "$SERVER_USER@$SERVER_IP:$remote_file"
}

# 1. Copy new ETL files
echo "📋 Step 1: Copying new ETL files..."
copy_to_server "docker/etl/bi_daily_import.py" "$PROJECT_PATH/docker/etl/bi_daily_import.py"
copy_to_server "docker/etl/Dockerfile" "$PROJECT_PATH/docker/etl/Dockerfile"
copy_to_server "docker-compose.yml" "$PROJECT_PATH/docker-compose.yml"
copy_to_server "scripts/daily_bi_import.sh" "$PROJECT_PATH/scripts/daily_bi_import.sh"
echo "✅ Files copied successfully"

# 2. Make script executable on server
echo "📋 Step 2: Setting permissions..."
run_remote "chmod +x $PROJECT_PATH/scripts/daily_bi_import.sh"
echo "✅ Permissions set"

# 3. Stop existing ETL container
echo "📋 Step 3: Stopping existing containers..."
run_remote "cd $PROJECT_PATH && docker-compose stop etl 2>/dev/null || true"
run_remote "cd $PROJECT_PATH && docker-compose rm -f etl 2>/dev/null || true"
echo "✅ Containers stopped"

# 4. Rebuild ETL container
echo "📋 Step 4: Rebuilding ETL container..."
run_remote "cd $PROJECT_PATH && docker-compose build etl"
echo "✅ ETL container rebuilt"

# 5. Test the new ETL process
echo "📋 Step 5: Testing BI import..."
run_remote "cd $PROJECT_PATH && timeout 300 docker-compose run --rm etl"
run_remote "cd $PROJECT_PATH && docker-compose rm -f etl 2>/dev/null || true"
echo "✅ Test import completed"

# 6. Set up cron job for daily execution
echo "📋 Step 6: Setting up daily cron job..."
CRON_COMMAND="0 6 * * * $PROJECT_PATH/scripts/daily_bi_import.sh"
run_remote "(crontab -l 2>/dev/null | grep -v 'daily_bi_import.sh' || true; echo '$CRON_COMMAND') | crontab -"
echo "✅ Cron job scheduled for 6:00 AM daily"

# 7. Verify deployment
echo "📋 Step 7: Verifying deployment..."
run_remote "cd $PROJECT_PATH && ls -la docker/etl/bi_daily_import.py scripts/daily_bi_import.sh"
run_remote "crontab -l | grep daily_bi_import.sh"
echo "✅ Deployment verified"

echo
echo "🎉 Daily BI Import Deployment Complete!"
echo
echo "📊 Summary:"
echo "   ✅ New ETL script deployed (bi_daily_import.py)"
echo "   ✅ Docker configuration updated"
echo "   ✅ Daily cron job scheduled (6:00 AM)"
echo "   ✅ Test import successful"
echo
echo "📈 The system will now automatically import these files daily:"
echo "   📄 BI Dimensions.xlsx → bi_dimensions table"
echo "   📄 BI At Scale Import.xlsx → bi_at_scale_import table"
echo
echo "🔍 To monitor:"
echo "   📝 Check logs: $PROJECT_PATH/logs/daily_bi_import_*.log"
echo "   📊 View data in Metabase: https://storemgnt.beachwood.me"
echo "   ⚙️  Manual run: $PROJECT_PATH/scripts/daily_bi_import.sh"
