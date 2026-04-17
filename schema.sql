-- ============================================================
-- HR Management System — PostgreSQL Schema (MINIMAL FIX)
-- ============================================================

-- 1. Companies
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    address TEXT,
    phone VARCHAR(30),
    email VARCHAR(150),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    company_secret VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Plans
CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) DEFAULT 0.00,
    features TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES plans(id),
    status TEXT DEFAULT 'trial',
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    external_subscription VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(150) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    role VARCHAR(50) DEFAULT 'HR',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    reset_token VARCHAR(255),
    reset_token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Departments
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Employees
CREATE TABLE IF NOT EXISTS employees_core (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    employee_code VARCHAR(50) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(30),
    department_id INTEGER REFERENCES departments(id),
    job_title VARCHAR(150),
    employment_type TEXT DEFAULT 'Full-Time',
    status TEXT DEFAULT 'Active',
    hire_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Attendance (IMPORTANT UNIQUE for upsert)
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees_core(id) ON DELETE CASCADE,
    work_date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    status TEXT DEFAULT 'Present',
    working_hours DECIMAL(5,2),
    notes VARCHAR(500),
    recorded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, employee_id, work_date)
);

-- 8. Leave Balances
CREATE TABLE IF NOT EXISTS leave_balances (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    employee_id INTEGER,
    year INTEGER,
    annual_total INTEGER DEFAULT 21,
    annual_used INTEGER DEFAULT 0
);

-- 9. Leave Requests
CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    employee_id INTEGER,
    leave_type TEXT,
    start_date DATE,
    end_date DATE,
    days_requested INTEGER,
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Compensation
CREATE TABLE IF NOT EXISTS compensation (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    employee_id INTEGER,
    basic_salary DECIMAL(15,2),
    currency CHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Payroll
CREATE TABLE IF NOT EXISTS payroll_runs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    employee_id INTEGER,
    pay_period VARCHAR(7),
    net_salary DECIMAL(15,2),
    status TEXT DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, employee_id, pay_period)
);

-- 12. Performance Reviews
CREATE TABLE IF NOT EXISTS performance_reviews (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    employee_id INTEGER,
    reviewer_id INTEGER,
    review_period VARCHAR(50),
    review_date DATE,
    overall_rating DECIMAL(3,1),
    status TEXT DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);