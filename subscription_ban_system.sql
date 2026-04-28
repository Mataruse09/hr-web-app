-- Add ban system and abuse tracking to companies table (MySQL Version)
-- Note: ALTER TABLE ADD COLUMN IF NOT EXISTS is not supported in MySQL, run separately
-- ALTER TABLE companies ADD COLUMN is_banned BOOLEAN DEFAULT FALSE;
-- ALTER TABLE companies ADD COLUMN ban_reason TEXT;
-- ALTER TABLE companies ADD COLUMN banned_at TIMESTAMP;
-- ALTER TABLE companies ADD COLUMN banned_by INTEGER;
-- ALTER TABLE companies ADD COLUMN ban_type VARCHAR(20) DEFAULT 'manual';
-- ALTER TABLE companies ADD COLUMN auto_ban_trigger VARCHAR(50);

-- Add abuse reports table
CREATE TABLE IF NOT EXISTS abuse_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER,
    reporter_id INTEGER,
    report_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    evidence JSON,
    status VARCHAR(20) DEFAULT 'pending',
    severity VARCHAR(20) DEFAULT 'low',
    resolved_by INTEGER,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add admin notifications table
CREATE TABLE IF NOT EXISTS admin_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info',
    is_read TINYINT(1) DEFAULT 0,
    link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add terms acceptance tracking
-- ALTER TABLE companies ADD COLUMN terms_accepted BOOLEAN DEFAULT FALSE;
-- ALTER TABLE companies ADD COLUMN terms_accepted_at TIMESTAMP;
-- ALTER TABLE companies ADD COLUMN terms_version VARCHAR(20);

-- Add subscription_plans with better pricing tiers (MySQL INSERT IGNORE)
INSERT IGNORE INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_employees, max_users, features, is_active, is_featured)
VALUES 
('starter', 'Starter', 'Perfect for small businesses starting their HR journey', 29, 290, 25, 5, '["employee_management", "attendance_tracking", "leave_management", "basic_reports"]', 1, 0),
('professional', 'Professional', 'For growing teams needing advanced features', 79, 790, 100, 15, '["employee_management", "attendance_tracking", "leave_management", "basic_reports", "payroll", "ai_analytics", "appraisals"]', 1, 1),
('enterprise', 'Enterprise', 'Full-featured solution for large organizations', 199, 1990, 500, 50, '["employee_management", "attendance_tracking", "leave_management", "basic_reports", "payroll", "ai_analytics", "appraisals", "forecasting", "gamification", "compliance", "advanced_security"]', 1, 0);

-- Update free plan limits
UPDATE subscription_plans SET max_employees = 10, max_users = 3, features = '["employee_management", "attendance_tracking", "leave_management"]' WHERE name = 'free';