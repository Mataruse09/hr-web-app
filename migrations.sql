-- ============================================================
-- HR APP UPGRADE MIGRATIONS — MySQL
-- Run this after the base schema.sql
-- ============================================================

-- 1. ACTIVITY/AUDIT LOG TABLE
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    user_id INTEGER,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. SYSTEM SETTINGS TABLE
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_company_setting (company_id, setting_key)
);

-- 3. ENHANCED PAYROLL TABLE (REPLACE existing payroll_runs)
-- Note: MySQL doesn't support ADD COLUMN IF NOT EXISTS, run these separately
-- ALTER TABLE payroll_runs ADD COLUMN basic_salary DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN gross_salary DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN overtime_hours DECIMAL(6,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN overtime_amount DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN prorated_salary DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN housing_allowance DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN transport_allowance DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN meal_allowance DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN performance_bonus DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN income_tax DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN social_security DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN health_insurance DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN other_deductions DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN net_salary DECIMAL(15,2) DEFAULT 0;
-- ALTER TABLE payroll_runs ADD COLUMN notes TEXT;
-- ALTER TABLE payroll_runs ADD COLUMN approved_by INTEGER;
-- ALTER TABLE payroll_runs ADD COLUMN approved_at TIMESTAMP;

-- 4. APPRAISAL/PERFORMANCE RATING TABLE
CREATE TABLE IF NOT EXISTS appraisals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    reviewer_id INTEGER,
    appraisal_period VARCHAR(50),
    rating DECIMAL(2,1),
    communication DECIMAL(2,1),
    teamwork DECIMAL(2,1),
    innovation DECIMAL(2,1),
    punctuality DECIMAL(2,1),
    overall_rating DECIMAL(3,2),
    comments TEXT,
    status VARCHAR(50) DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. LABOUR FORECASTING TABLE
CREATE TABLE IF NOT EXISTS labour_forecasts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    department_id INTEGER,
    forecast_month DATE,
    current_headcount INTEGER,
    projected_hires INTEGER,
    projected_exits INTEGER,
    projected_headcount INTEGER,
    hiring_budget DECIMAL(15,2),
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 6. ATTRITION TABLE
CREATE TABLE IF NOT EXISTS attrition_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    exit_date DATE,
    reason VARCHAR(255),
    exit_interview_notes TEXT,
    final_settlement_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. GAMIFICATION/POINTS TABLE
CREATE TABLE IF NOT EXISTS gamification_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    badges TEXT,
    achievements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 8. COMPLIANCE/POLICY TABLE
CREATE TABLE IF NOT EXISTS compliance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    employee_id INTEGER,
    policy_name VARCHAR(255),
    compliance_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    due_date DATE,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. AI PREDICTIONS LOG TABLE
CREATE TABLE IF NOT EXISTS ai_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INTEGER NOT NULL,
    prediction_type VARCHAR(100),
    parameters TEXT,
    result TEXT,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. USER ROLES TABLE (for granular RBAC)
CREATE TABLE IF NOT EXISTS user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_company_role (user_id, company_id, role)
);

-- 11. PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    permission VARCHAR(100) NOT NULL,
    UNIQUE KEY unique_role_permission (role, permission)
);

-- 12. EMPLOYEE EXTENDED INFO (Personal details access control)
-- Note: MySQL doesn't support ADD COLUMN IF NOT EXISTS, run these separately
-- ALTER TABLE employees_core ADD COLUMN date_of_birth DATE;
-- ALTER TABLE employees_core ADD COLUMN gender VARCHAR(50);
-- ALTER TABLE employees_core ADD COLUMN nationality VARCHAR(100);
-- ALTER TABLE employees_core ADD COLUMN bank_account VARCHAR(50);
-- ALTER TABLE employees_core ADD COLUMN tax_id VARCHAR(50);
-- ALTER TABLE employees_core ADD COLUMN emergency_contact VARCHAR(100);
-- ALTER TABLE employees_core ADD COLUMN emergency_contact_phone VARCHAR(30);

-- 13. INDEXES FOR PERFORMANCE
CREATE INDEX idx_activity_logs_company ON activity_logs(company_id, created_at DESC);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_payroll_company ON payroll_runs(company_id, pay_period);
CREATE INDEX idx_appraisals_employee ON appraisals(employee_id);
CREATE INDEX idx_forecasts_company ON labour_forecasts(company_id, forecast_month);
CREATE INDEX idx_attrition_company ON attrition_records(company_id);
CREATE INDEX idx_compliance_company ON compliance_records(company_id);

-- 14. INSERT DEFAULT PERMISSIONS
INSERT IGNORE INTO permissions (role, permission) VALUES
    ('Admin', 'view_all_employees'),
    ('Admin', 'edit_all_employees'),
    ('Admin', 'view_payroll'),
    ('Admin', 'edit_payroll'),
    ('Admin', 'view_activity_logs'),
    ('Admin', 'manage_system_settings'),
    ('Admin', 'manage_users'),
    ('Admin', 'view_analytics'),
    ('HR', 'view_all_employees'),
    ('HR', 'edit_all_employees'),
    ('HR', 'view_payroll'),
    ('HR', 'view_activity_logs'),
    ('HR', 'manage_appraisals'),
    ('HR', 'view_analytics'),
    ('Manager', 'view_department_employees'),
    ('Manager', 'mark_attendance'),
    ('Manager', 'view_team_payroll'),
    ('CHRO', 'view_all_employees'),
    ('CHRO', 'view_payroll'),
    ('CHRO', 'manage_appraisals'),
    ('CHRO', 'view_analytics'),
    ('Employee', 'view_own_profile'),
    ('Employee', 'view_own_attendance'),
    ('Employee', 'view_own_payroll'),
    ('Employee', 'request_leave'),
    ('Employee', 'view_own_appraisal');

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
