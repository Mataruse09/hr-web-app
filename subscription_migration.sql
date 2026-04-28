-- Subscription and Feature Gating System (MySQL Version)
-- This migration adds subscription plans and feature access control

-- Create subscription_plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    price_yearly DECIMAL(10, 2),
    max_employees INTEGER NOT NULL DEFAULT 10,
    max_users INTEGER NOT NULL DEFAULT 5,
    features JSON NOT NULL DEFAULT '[]',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_trial TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create company_subscriptions table
CREATE TABLE IF NOT EXISTS company_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew TINYINT(1) NOT NULL DEFAULT 1,
    cancel_at_period_end TINYINT(1) NOT NULL DEFAULT 0,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create subscription_features table to track which features are available
CREATE TABLE IF NOT EXISTS subscription_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    is_premium TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default subscription plans (use INSERT IGNORE for MySQL)
INSERT IGNORE INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_employees, max_users, features, is_active, is_trial) VALUES
('free', 'Free Plan', 'Basic HR features for small teams', 0, 0, 10, 3, '["employees", "attendance", "leave", "basic_reports"]', 1, 0),
('starter', 'Starter Plan', 'Essential HR features for growing teams', 29.99, 299.99, 50, 10, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals"]', 1, 0),
('professional', 'Professional Plan', 'Advanced HR with AI analytics', 79.99, 799.99, 200, 25, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition"]', 1, 0),
('enterprise', 'Enterprise Plan', 'Full-featured HR for large organizations', 199.99, 1999.99, 1000, 100, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition", "compliance", "gamification", "advanced_forecasting"]', 1, 0);

-- Insert subscription features (use INSERT IGNORE for MySQL)
INSERT IGNORE INTO subscription_features (name, display_name, description, category, is_premium) VALUES
('employees', 'Employee Management', 'Basic employee CRUD operations', 'basic', 0),
('attendance', 'Attendance Tracking', 'Track employee attendance and hours', 'basic', 0),
('leave', 'Leave Management', 'Manage employee leave requests', 'basic', 0),
('basic_reports', 'Basic Reports', 'Standard HR reports and dashboards', 'basic', 0),
('payroll', 'Payroll', 'Payroll processing and management', 'advanced', 1),
('appraisals', 'Appraisals', 'Performance appraisal system', 'advanced', 1),
('ai_analytics', 'AI Analytics', 'AI-powered workforce insights', 'ai', 1),
('forecasting', 'Labour Forecasting', 'Workforce demand forecasting', 'ai', 1),
('attrition', 'Attrition Analysis', 'Employee attrition risk analysis', 'ai', 1),
('compliance', 'Compliance Management', 'Regulatory compliance tracking', 'premium', 1),
('gamification', 'Gamification', 'Employee engagement and rewards', 'premium', 1),
('advanced_forecasting', 'Advanced Forecasting', 'ML-powered workforce predictions', 'ai', 1);

-- Add subscription columns to companies table (MySQL way - check first)
-- Note: These must be run separately in MySQL
-- ALTER TABLE companies ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'trial';
-- ALTER TABLE companies ADD COLUMN plan_id INTEGER;
-- ALTER TABLE companies ADD COLUMN subscription_start DATE;
-- ALTER TABLE companies ADD COLUMN subscription_end DATE;

-- Create indexes
CREATE INDEX idx_company_subscriptions_company ON company_subscriptions(company_id);
CREATE INDEX idx_company_subscriptions_status ON company_subscriptions(status);