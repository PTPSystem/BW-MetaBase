-- Initialize the Metabase database with sample store data
-- This script creates tables and inserts sample data for demonstration

-- Create additional database for sample business data
CREATE DATABASE IF NOT EXISTS bw_sample_data;

-- Connect to the sample data database
\c bw_sample_data;

-- Create stores table
CREATE TABLE IF NOT EXISTS stores (
    store_id VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    region VARCHAR(50),
    district VARCHAR(50),
    opened_date DATE,
    manager_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user-store relationship table
CREATE TABLE IF NOT EXISTS user_store_access (
    user_id INTEGER REFERENCES users(user_id),
    store_id VARCHAR(10) REFERENCES stores(store_id),
    access_level VARCHAR(50) DEFAULT 'read',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(user_id),
    PRIMARY KEY (user_id, store_id)
);

-- Create sales data table (similar to existing patterns)
CREATE TABLE IF NOT EXISTS daily_sales (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(10) REFERENCES stores(store_id),
    sale_date DATE NOT NULL,
    day_part VARCHAR(20) NOT NULL, -- Morning, Lunch, Afternoon, Evening
    day_of_week INTEGER NOT NULL, -- 1=Monday, 7=Sunday
    net_sales_usd DECIMAL(10,2),
    transaction_count INTEGER,
    average_ticket DECIMAL(10,2),
    labor_hours DECIMAL(8,2),
    labor_cost DECIMAL(10,2),
    food_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, sale_date, day_part)
);

-- Create labor forecast table (following existing patterns)
CREATE TABLE IF NOT EXISTS labor_forecast (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(10) REFERENCES stores(store_id),
    fiscal_year INTEGER NOT NULL,
    fiscal_week INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_part VARCHAR(20) NOT NULL,
    planned_headcount DECIMAL(8,2),
    planned_labor_percent DECIMAL(5,2),
    planned_wage DECIMAL(10,2),
    planned_hours DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, fiscal_year, fiscal_week, day_of_week, day_part)
);

-- Create sales forecast table (following existing patterns)
CREATE TABLE IF NOT EXISTS sales_forecast (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(10) REFERENCES stores(store_id),
    fiscal_week VARCHAR(10) NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_part VARCHAR(20) NOT NULL,
    forecasted_sales DECIMAL(10,2),
    confidence_interval_lower DECIMAL(10,2),
    confidence_interval_upper DECIMAL(10,2),
    model_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, fiscal_week, day_of_week, day_part)
);

-- Insert sample stores (using 6-digit format from existing system)
INSERT INTO stores (store_id, store_name, location, region, district, opened_date, manager_name, phone, email) VALUES
('000001', 'Downtown Beachwood', '123 Main St, Beachwood, OH', 'Northeast', 'Cleveland', '2020-01-15', 'John Smith', '(216) 555-0101', 'downtown@beachwood.me'),
('000002', 'Westside Plaza', '456 West Ave, Cleveland, OH', 'Northeast', 'Cleveland', '2019-03-22', 'Sarah Johnson', '(216) 555-0102', 'westside@beachwood.me'),
('000003', 'Suburban Center', '789 Suburban Rd, Shaker Heights, OH', 'Northeast', 'Cleveland', '2021-06-10', 'Mike Davis', '(216) 555-0103', 'suburban@beachwood.me'),
('000004', 'Highway Junction', '321 Highway 1, Akron, OH', 'Northeast', 'Akron', '2018-11-05', 'Lisa Brown', '(330) 555-0104', 'highway@beachwood.me'),
('000005', 'University District', '654 University Blvd, Kent, OH', 'Northeast', 'Akron', '2022-02-28', 'David Wilson', '(330) 555-0105', 'university@beachwood.me');

-- Insert sample users
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@beachwood.me', '$2b$12$example_hash_for_admin', 'System Administrator', 'admin'),
('jsmith', 'john.smith@beachwood.me', '$2b$12$example_hash_for_jsmith', 'John Smith', 'manager'),
('sjohnson', 'sarah.johnson@beachwood.me', '$2b$12$example_hash_for_sjohnson', 'Sarah Johnson', 'manager'),
('regional1', 'regional1@beachwood.me', '$2b$12$example_hash_for_regional1', 'Regional Manager 1', 'regional'),
('analyst1', 'analyst1@beachwood.me', '$2b$12$example_hash_for_analyst1', 'Business Analyst', 'analyst');

-- Insert user-store access relationships
-- Admin has access to all stores
INSERT INTO user_store_access (user_id, store_id, access_level, granted_by) VALUES
(1, '000001', 'admin', 1),
(1, '000002', 'admin', 1),
(1, '000003', 'admin', 1),
(1, '000004', 'admin', 1),
(1, '000005', 'admin', 1);

-- Managers have access to their specific stores
INSERT INTO user_store_access (user_id, store_id, access_level, granted_by) VALUES
(2, '000001', 'manager', 1),  -- John Smith - Downtown
(3, '000002', 'manager', 1);  -- Sarah Johnson - Westside

-- Regional manager has access to Cleveland district stores
INSERT INTO user_store_access (user_id, store_id, access_level, granted_by) VALUES
(4, '000001', 'read', 1),
(4, '000002', 'read', 1),
(4, '000003', 'read', 1);

-- Analyst has read access to all stores
INSERT INTO user_store_access (user_id, store_id, access_level, granted_by) VALUES
(5, '000001', 'read', 1),
(5, '000002', 'read', 1),
(5, '000003', 'read', 1),
(5, '000004', 'read', 1),
(5, '000005', 'read', 1);

-- Insert sample sales data (30 days worth for each store)
-- This generates realistic sample data similar to existing patterns
DO $$
DECLARE
    store_rec RECORD;
    date_counter DATE;
    day_parts TEXT[] := ARRAY['Morning', 'Lunch', 'Afternoon', 'Evening'];
    part TEXT;
    base_sales DECIMAL;
    dow INTEGER;
BEGIN
    FOR store_rec IN SELECT store_id FROM stores LOOP
        date_counter := CURRENT_DATE - INTERVAL '30 days';
        WHILE date_counter <= CURRENT_DATE LOOP
            dow := EXTRACT(DOW FROM date_counter);
            IF dow = 0 THEN dow := 7; END IF; -- Convert Sunday from 0 to 7
            
            FOREACH part IN ARRAY day_parts LOOP
                -- Generate realistic sales data based on day part and day of week
                base_sales := CASE 
                    WHEN part = 'Morning' THEN 800 + (RANDOM() * 400)
                    WHEN part = 'Lunch' THEN 1500 + (RANDOM() * 800)
                    WHEN part = 'Afternoon' THEN 600 + (RANDOM() * 300)
                    WHEN part = 'Evening' THEN 1200 + (RANDOM() * 600)
                END;
                
                -- Weekend multiplier
                IF dow IN (6, 7) THEN
                    base_sales := base_sales * 1.3;
                END IF;
                
                INSERT INTO daily_sales (
                    store_id, sale_date, day_part, day_of_week,
                    net_sales_usd, transaction_count, average_ticket,
                    labor_hours, labor_cost, food_cost
                ) VALUES (
                    store_rec.store_id,
                    date_counter,
                    part,
                    dow,
                    ROUND(base_sales, 2),
                    ROUND(base_sales / (15 + RANDOM() * 10)),  -- Average ticket ~$15-25
                    ROUND(base_sales / (15 + RANDOM() * 10), 2),
                    ROUND(8 + RANDOM() * 16, 2),  -- 8-24 hours per day part
                    ROUND((8 + RANDOM() * 16) * (12 + RANDOM() * 8), 2), -- $12-20/hour
                    ROUND(base_sales * (0.25 + RANDOM() * 0.1), 2) -- 25-35% food cost
                );
            END LOOP;
            date_counter := date_counter + INTERVAL '1 day';
        END LOOP;
    END LOOP;
END $$;

-- Create indexes for better performance
CREATE INDEX idx_daily_sales_store_date ON daily_sales(store_id, sale_date);
CREATE INDEX idx_daily_sales_dow_part ON daily_sales(day_of_week, day_part);
CREATE INDEX idx_user_store_access_user ON user_store_access(user_id);
CREATE INDEX idx_labor_forecast_store_week ON labor_forecast(store_id, fiscal_year, fiscal_week);
CREATE INDEX idx_sales_forecast_store_week ON sales_forecast(store_id, fiscal_week);

-- Grant permissions to metabase user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO metabase;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO metabase;
