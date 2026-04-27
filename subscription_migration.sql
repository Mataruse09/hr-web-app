-- Subscription and Feature Gating System
-- This migration adds subscription plans and feature access control

-- Create subscription_plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    price_yearly DECIMAL(10, 2),
    max_employees INTEGER NOT NULL DEFAULT 10,
    max_users INTEGER NOT NULL DEFAULT 5,
    features JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_trial BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create company_subscriptions table
CREATE TABLE IF NOT EXISTS company_subscriptions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, trial, expired, cancelled, past_due
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create subscription_features table to track which features are available
CREATE TABLE IF NOT EXISTS subscription_features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- ai, advanced, basic, premium
    is_premium BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default subscription plans
INSERT INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_employees, max_users, features, is_active, is_trial) VALUES
('free', 'Free Plan', 'Basic HR features for small teams', 0, 0, 10, 3, '["employees", "attendance", "leave", "basic_reports"]', true, false),
('starter', 'Starter Plan', 'Essential HR features for growing teams', 29.99, 299.99, 50, 10, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals"]', true, false),
('professional', 'Professional Plan', 'Advanced HR with AI analytics', 79.99, 799.99, 200, 25, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition"]', true, false),
('enterprise', 'Enterprise Plan', 'Full-featured HR for large organizations', 199.99, 1999.99, 1000, 100, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition", "compliance", "gamification", "advanced_forecasting"]', true, false)
ON CONFLICT (name) DO NOTHING;

-- Insert subscription features
INSERT INTO subscription_features (name, display_name, description, category, is_premium) VALUES
('employees', 'Employee Management', 'Basic employee CRUD operations', 'basic', false),
('attendance', 'Attendance Tracking', 'Track employee attendance and hours', 'basic', false),
('leave', 'Leave Management', 'Manage employee leave requests', 'basic', false),
('basic_reports', 'Basic Reports', 'Standard HR reports and dashboards', 'basic', false),
('payroll', 'Payroll', 'Payroll processing and management', 'advanced', true),
('appraisals', 'Appraisals', 'Performance appraisal system', 'advanced', true),
('ai_analytics', 'AI Analytics', 'AI-powered workforce insights', 'ai', true),
('forecasting', 'Labour Forecasting', 'Workforce demand forecasting', 'ai', true),
('attrition', 'Attrition Analysis', 'Employee attrition risk analysis', 'ai', true),
('compliance', 'Compliance Management', 'Regulatory compliance tracking', 'premium', true),
('gamification', 'Gamification', 'Employee engagement and rewards', 'premium', true),
('advanced_forecasting', 'Advanced Forecasting', 'ML-powered workforce predictions', 'ai', true)
ON CONFLICT (name) DO NOTHING;

-- Add subscription columns to companies table (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'companies' AND column_name = 'subscription_status') THEN
        ALTER TABLE companies ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'trial';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'companies' AND column_name = 'plan_id') THEN
        ALTER TABLE companies ADD COLUMN plan_id INTEGER REFERENCES subscription_plans(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'companies' AND column_name = 'subscription_start') THEN
        ALTER TABLE companies ADD COLUMN subscription_start DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'companies' AND column_name = 'subscription_end') THEN
        ALTER TABLE companies ADD COLUMN subscription_end DATE;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_company ON company_subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status ON company_subscriptions(status);