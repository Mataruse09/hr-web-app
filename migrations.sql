-- ============================================================
-- HR APP UPGRADE MIGRATIONS — PostgreSQL
-- Run this after the base schema.sql
-- ============================================================

-- 1. ACTIVITY/AUDIT LOG TABLE
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, setting_key)
);

-- 3. ENHANCED PAYROLL TABLE (REPLACE existing payroll_runs)
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    basic_salary DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    gross_salary DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    overtime_hours DECIMAL(6,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    overtime_amount DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    prorated_salary DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    housing_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    transport_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    meal_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    performance_bonus DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    income_tax DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    social_security DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    health_insurance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    other_deductions DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    net_salary DECIMAL(15,2) DEFAULT 0;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    notes TEXT;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS
    approved_at TIMESTAMP;

-- 4. APPRAISAL/PERFORMANCE RATING TABLE
CREATE TABLE IF NOT EXISTS appraisals (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees_core(id) ON DELETE CASCADE,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. LABOUR FORECASTING TABLE
CREATE TABLE IF NOT EXISTS labour_forecasts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    forecast_month DATE,
    current_headcount INTEGER,
    projected_hires INTEGER,
    projected_exits INTEGER,
    projected_headcount INTEGER,
    hiring_budget DECIMAL(15,2),
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ATTRITION TABLE
CREATE TABLE IF NOT EXISTS attrition_records (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees_core(id) ON DELETE CASCADE,
    exit_date DATE,
    reason VARCHAR(255),
    exit_interview_notes TEXT,
    final_settlement_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. GAMIFICATION/POINTS TABLE
CREATE TABLE IF NOT EXISTS gamification_points (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees_core(id) ON DELETE CASCADE,
    points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    badges TEXT,
    achievements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. COMPLIANCE/POLICY TABLE
CREATE TABLE IF NOT EXISTS compliance_records (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees_core(id) ON DELETE CASCADE,
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
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    prediction_type VARCHAR(100),
    parameters TEXT,
    result TEXT,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. USER ROLES TABLE (for granular RBAC)
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, company_id, role)
);

-- 11. PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    permission VARCHAR(100) NOT NULL,
    UNIQUE(role, permission)
);

-- 12. EMPLOYEE EXTENDED INFO (Personal details access control)
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    date_of_birth DATE;
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    gender VARCHAR(50);
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    nationality VARCHAR(100);
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    bank_account VARCHAR(50);
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    tax_id VARCHAR(50);
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    emergency_contact VARCHAR(100);
ALTER TABLE employees_core ADD COLUMN IF NOT EXISTS
    emergency_contact_phone VARCHAR(30);

-- 13. INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_activity_logs_company ON activity_logs(company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_payroll_company ON payroll_runs(company_id, pay_period);
CREATE INDEX IF NOT EXISTS idx_appraisals_employee ON appraisals(employee_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_company ON labour_forecasts(company_id, forecast_month);
CREATE INDEX IF NOT EXISTS idx_attrition_company ON attrition_records(company_id);
CREATE INDEX IF NOT EXISTS idx_compliance_company ON compliance_records(company_id);

-- 14. INSERT DEFAULT PERMISSIONS
INSERT INTO permissions (role, permission) VALUES
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
