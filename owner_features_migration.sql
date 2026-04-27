-- Migration: Add subscription management columns
-- Run this to enable all owner dashboard subscription features

-- Add columns to company_subscriptions table for free access tracking
ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS is_global_free BOOLEAN DEFAULT FALSE;
ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS free_access_until TIMESTAMP NULL;

-- Add columns to companies table for ban tracking (if not exist)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ban_reason TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP NULL;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS banned_by INTEGER;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ban_type VARCHAR(50) DEFAULT 'manual';

-- Note: activity_logs table already exists and is used by company admins
-- The owner dashboard will read from the same activity_logs table

-- blocked_ips table already created by owner_security.sql
-- Just add is_active column if not exists
ALTER TABLE blocked_ips ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Create abuse_reports table if not exists (for reporting misuse)
CREATE TABLE IF NOT EXISTS abuse_reports (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    description TEXT,
    severity VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    reported_by INTEGER,
    resolved_by INTEGER,
    resolution_notes TEXT,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_abuse_reports_company_id ON abuse_reports(company_id);
CREATE INDEX IF NOT EXISTS idx_abuse_reports_status ON abuse_reports(status);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_company_id ON company_subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_end_date ON company_subscriptions(end_date);

-- Insert default subscription plans if not exist
INSERT INTO subscription_plans (name, price_monthly, price_yearly, max_employees, features, is_active) 
VALUES 
('Starter', 29.00, 290.00, 10, 'Basic HR features, Up to 10 employees, Email support', TRUE),
('Professional', 79.00, 790.00, 50, 'Advanced HR features, Up to 50 employees, Priority support, Analytics', TRUE),
('Enterprise', 199.00, 1990.00, 999999, 'Full HR suite, Unlimited employees, 24/7 support, Custom integrations', TRUE)
ON CONFLICT DO NOTHING;

SELECT 'Migration completed successfully!' as result;