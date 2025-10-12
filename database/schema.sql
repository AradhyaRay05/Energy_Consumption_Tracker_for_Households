-- Energy Consumption Tracker Database Schema
-- MySQL Database Setup

-- Create Database
CREATE DATABASE IF NOT EXISTS energy_tracker;
USE energy_tracker;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    household_size INT DEFAULT 1,
    tariff_rate DECIMAL(10, 4) DEFAULT 0.12, -- Cost per kWh in dollars
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Energy Data Table (Historical consumption records)
CREATE TABLE IF NOT EXISTS energy_data (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    appliance_name VARCHAR(100) NOT NULL,
    power_usage_kwh DECIMAL(10, 4) NOT NULL, -- Energy consumed in kWh
    cost DECIMAL(10, 2) NOT NULL, -- Cost in dollars
    duration_hours DECIMAL(6, 2) DEFAULT 1.0, -- How long the appliance ran
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_appliance (appliance_name),
    INDEX idx_timestamp (timestamp)
);

-- Predictions Table (ML-generated predictions)
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    prediction_date DATE NOT NULL,
    predicted_consumption_kwh DECIMAL(10, 4) NOT NULL,
    predicted_cost DECIMAL(10, 2) NOT NULL,
    confidence_score DECIMAL(5, 4), -- Model confidence (0-1)
    prediction_type VARCHAR(20) DEFAULT 'daily', -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, prediction_date),
    INDEX idx_prediction_type (prediction_type)
);

-- Appliances Reference Table (Common appliances and their typical power ratings)
CREATE TABLE IF NOT EXISTS appliances (
    appliance_id INT AUTO_INCREMENT PRIMARY KEY,
    appliance_name VARCHAR(100) UNIQUE NOT NULL,
    typical_power_watts INT NOT NULL, -- Typical power consumption in watts
    category VARCHAR(50), -- e.g., Kitchen, Entertainment, Climate Control
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insights Table (Personalized recommendations)
CREATE TABLE IF NOT EXISTS insights (
    insight_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    insight_text TEXT NOT NULL,
    insight_type VARCHAR(50), -- e.g., 'cost_saving', 'peak_usage', 'appliance_alert'
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_unread (user_id, is_read)
);

-- Insert Default Appliances
INSERT INTO appliances (appliance_name, typical_power_watts, category, description) VALUES
('Air Conditioner', 3500, 'Climate Control', 'Central air conditioning unit'),
('Space Heater', 1500, 'Climate Control', 'Portable space heater'),
('Refrigerator', 150, 'Kitchen', '24/7 running refrigerator'),
('Washing Machine', 500, 'Laundry', 'Front-load washing machine'),
('Dryer', 3000, 'Laundry', 'Electric clothes dryer'),
('Dishwasher', 1800, 'Kitchen', 'Standard dishwasher'),
('Microwave', 1000, 'Kitchen', 'Microwave oven'),
('Electric Oven', 2400, 'Kitchen', 'Electric cooking oven'),
('Television', 150, 'Entertainment', 'LED TV 50 inch'),
('Computer', 200, 'Electronics', 'Desktop computer'),
('Laptop', 50, 'Electronics', 'Laptop computer'),
('Water Heater', 4000, 'Climate Control', 'Electric water heater'),
('LED Lights', 10, 'Lighting', 'LED bulb per unit'),
('Vacuum Cleaner', 1400, 'Cleaning', 'Upright vacuum'),
('Hair Dryer', 1500, 'Personal Care', 'Standard hair dryer'),
('Iron', 1100, 'Laundry', 'Steam iron'),
('Coffee Maker', 1000, 'Kitchen', 'Drip coffee maker'),
('Toaster', 1200, 'Kitchen', 'Two-slice toaster'),
('Gaming Console', 150, 'Entertainment', 'Modern gaming console'),
('Router', 10, 'Electronics', 'WiFi router');

-- Insert Sample User (Password: password123 - hashed with bcrypt)
INSERT INTO users (username, email, password_hash, full_name, household_size, tariff_rate) VALUES
('demo_user', 'demo@energytracker.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5WzvjxGZ7RQzu', 'Demo User', 3, 0.12);

-- Create Views for Common Queries

-- View: Daily consumption summary per user
CREATE OR REPLACE VIEW daily_consumption AS
SELECT 
    user_id,
    DATE(timestamp) as date,
    SUM(power_usage_kwh) as total_kwh,
    SUM(cost) as total_cost,
    COUNT(DISTINCT appliance_name) as appliances_used,
    COUNT(*) as total_records
FROM energy_data
GROUP BY user_id, DATE(timestamp);

-- View: Appliance-wise consumption per user
CREATE OR REPLACE VIEW appliance_consumption AS
SELECT 
    user_id,
    appliance_name,
    SUM(power_usage_kwh) as total_kwh,
    SUM(cost) as total_cost,
    COUNT(*) as usage_count,
    AVG(power_usage_kwh) as avg_kwh_per_use
FROM energy_data
GROUP BY user_id, appliance_name;

-- View: Monthly statistics per user
CREATE OR REPLACE VIEW monthly_statistics AS
SELECT 
    user_id,
    YEAR(timestamp) as year,
    MONTH(timestamp) as month,
    SUM(power_usage_kwh) as total_kwh,
    SUM(cost) as total_cost,
    AVG(power_usage_kwh) as avg_daily_kwh,
    MAX(power_usage_kwh) as peak_kwh
FROM energy_data
GROUP BY user_id, YEAR(timestamp), MONTH(timestamp);
