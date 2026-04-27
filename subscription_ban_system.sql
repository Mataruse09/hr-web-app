-- Add ban system and abuse tracking to companies table
ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ban_reason TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS banned_by INTEGER;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ban_type VARCHAR(20) DEFAULT 'manual'; -- 'manual' or 'auto'
ALTER TABLE companies ADD COLUMN IF NOT EXISTS auto_ban_trigger VARCHAR(50); -- reason for auto ban

-- Add abuse reports table
CREATE TABLE IF NOT EXISTS abuse_reports (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    reporter_id INTEGER REFERENCES users(id),
    report_type VARCHAR(50) NOT NULL, -- 'terms_violation', 'spam', 'abuse', 'illegal_content', 'fraud'
    description TEXT NOT NULL,
    evidence JSONB, -- store evidence URLs, screenshots, etc.
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'investigating', 'resolved', 'dismissed'
    severity VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add admin notifications table
CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info', -- 'info', 'warning', 'abuse', 'ban', 'subscription'
    is_read BOOLEAN DEFAULT FALSE,
    link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add terms acceptance tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS terms_accepted BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS terms_version VARCHAR(20);

-- Add subscription_plans with better pricing tiers
INSERT INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_employees, max_users, features, is_active, is_featured)
VALUES 
('starter', 'Starter', 'Perfect for small businesses starting their HR journey', 29, 290, 25, 5, '["employee_management", "attendance_tracking", "leave_management", "basic_reports"]', TRUE, FALSE),
('professional', 'Professional', 'For growing teams needing advanced features', 79, 790, 100, 15, '["employee_management", "attendance_tracking", "leave_management", "basic_reports", "payroll", "ai_analytics", "appraisals"]', TRUE, TRUE),
('enterprise', 'Enterprise', 'Full-featured solution for large organizations', 199, 1990, 500, 50, '["employee_management", "attendance_tracking", "leave_management", "basic_reports", "payroll", "ai_analytics", "appraisals", "forecasting", "gamification", "compliance", "advanced_security"]', TRUE, FALSE)
ON CONFLICT (name) DO UPDATE SET 
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    max_employees = EXCLUDED.max_employees,
    max_users = EXCLUDED.max_users,
    features = EXCLUDED.features,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- Update free plan limits
UPDATE subscription_plans SET max_employees = 10, max_users = 3, features = '["employee_management", "attendance_tracking", "leave_management"]' WHERE name = 'free';