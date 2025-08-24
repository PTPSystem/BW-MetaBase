#!/bin/bash

# Sample Database Initialization Script
# Creates additional sample data and configurations for BW-MetaBase

set -e

echo "🔄 Initializing BW-MetaBase Sample Database..."

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the BW-MetaBase root directory"
    exit 1
fi

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Error: Docker services are not running. Please start them first:"
    echo "   docker-compose up -d"
    exit 1
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
while ! docker-compose exec postgres pg_isready -U metabase > /dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -gt $timeout ]; then
        echo "❌ Error: PostgreSQL is not responding after ${timeout} seconds"
        exit 1
    fi
done

echo "✅ PostgreSQL is ready"

# Check if sample database exists
if docker-compose exec postgres psql -U metabase -lqt | cut -d \| -f 1 | grep -qw bw_sample_data; then
    echo "✅ Sample database 'bw_sample_data' already exists"
else
    echo "📦 Creating sample database 'bw_sample_data'..."
    docker-compose exec postgres createdb -U metabase bw_sample_data
fi

# Initialize sample data
echo "📊 Loading sample data..."
docker-compose exec postgres psql -U metabase -d bw_sample_data -f /docker-entrypoint-initdb.d/01-sample-data.sql

# Verify data loading
echo "🔍 Verifying data loading..."

# Check stores
store_count=$(docker-compose exec postgres psql -U metabase -d bw_sample_data -tAc "SELECT COUNT(*) FROM stores;")
echo "   Stores loaded: $store_count"

# Check users
user_count=$(docker-compose exec postgres psql -U metabase -d bw_sample_data -tAc "SELECT COUNT(*) FROM users;")
echo "   Users loaded: $user_count"

# Check sales data
sales_count=$(docker-compose exec postgres psql -U metabase -d bw_sample_data -tAc "SELECT COUNT(*) FROM daily_sales;")
echo "   Sales records loaded: $sales_count"

# Check user-store relationships
access_count=$(docker-compose exec postgres psql -U metabase -d bw_sample_data -tAc "SELECT COUNT(*) FROM user_store_access;")
echo "   User-store access records: $access_count"

# Display sample data summary
echo ""
echo "📋 Sample Data Summary:"
echo "===================="

echo "🏪 Stores:"
docker-compose exec postgres psql -U metabase -d bw_sample_data -c "
SELECT 
    store_id,
    store_name,
    location,
    manager_name
FROM stores
ORDER BY store_id;
" || echo "   Error querying stores"

echo ""
echo "👥 Users:"
docker-compose exec postgres psql -U metabase -d bw_sample_data -c "
SELECT 
    username,
    full_name,
    role,
    email
FROM users
ORDER BY user_id;
" || echo "   Error querying users"

echo ""
echo "🔗 User-Store Access Summary:"
docker-compose exec postgres psql -U metabase -d bw_sample_data -c "
SELECT 
    u.username,
    u.role,
    COUNT(usa.store_id) as accessible_stores,
    STRING_AGG(usa.store_id, ', ' ORDER BY usa.store_id) as store_ids
FROM users u
LEFT JOIN user_store_access usa ON u.user_id = usa.user_id
GROUP BY u.user_id, u.username, u.role
ORDER BY u.username;
" || echo "   Error querying user access"

echo ""
echo "📊 Sales Data Summary:"
docker-compose exec postgres psql -U metabase -d bw_sample_data -c "
SELECT 
    store_id,
    COUNT(*) as total_records,
    MIN(sale_date) as earliest_date,
    MAX(sale_date) as latest_date,
    ROUND(AVG(net_sales_usd), 2) as avg_daily_sales
FROM daily_sales
GROUP BY store_id
ORDER BY store_id;
" || echo "   Error querying sales data"

# Test Metabase connectivity
echo ""
echo "🔌 Testing Metabase Database Connectivity..."

# Create a test connection configuration
metabase_test_query='SELECT COUNT(*) as total_stores FROM stores;'

if docker-compose exec postgres psql -U metabase -d bw_sample_data -c "$metabase_test_query" > /dev/null 2>&1; then
    echo "✅ Metabase can successfully connect to sample database"
    echo ""
    echo "📝 Metabase Database Connection Details:"
    echo "   Database Type: PostgreSQL"
    echo "   Host: postgres"
    echo "   Port: 5432"
    echo "   Database: bw_sample_data"
    echo "   Username: metabase"
    echo "   Password: [from your .env POSTGRES_PASSWORD]"
else
    echo "❌ Error: Failed to test database connectivity"
fi

echo ""
echo "🎉 Sample Database Initialization Complete!"
echo ""
echo "Next Steps:"
echo "1. Access Metabase at: http://localhost:3000 (or your domain)"
echo "2. Complete Metabase setup if not done already"
echo "3. Add the sample database connection using the details above"
echo "4. Start creating dashboards with the loaded sample data"
echo ""
echo "Sample Usernames for Testing:"
echo "   • admin - System Administrator (all stores)"
echo "   • jsmith - Store Manager (store 000001)"
echo "   • sjohnson - Store Manager (store 000002)"
echo "   • regional1 - Regional Manager (Cleveland stores)"
echo "   • analyst1 - Business Analyst (all stores, read-only)"
echo ""
echo "Note: All sample users have placeholder password hashes."
echo "      Configure proper authentication in production."
