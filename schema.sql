-- ============================================================
-- HR Management System — MySQL Schema
-- ============================================================
USE railway;

-- ─────────────────────────────────────────────────────────────
-- 1. Companies
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    industry    VARCHAR(100),
    address     TEXT,
    phone       VARCHAR(30),
    email       VARCHAR(150),
    website     VARCHAR(255),
    is_active        TINYINT(1)  NOT NULL DEFAULT 1,
    company_secret   VARCHAR(255) NULL,
    created_at       TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_active (is_active)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 1.5. Subscription plans
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plans (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    price       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    features    TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subscriptions (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id            INT UNSIGNED NOT NULL,
    plan_id               INT UNSIGNED NOT NULL,
    status                ENUM('active','past_due','cancelled','trial','expired') NOT NULL DEFAULT 'trial',
    started_at            DATETIME NOT NULL,
    expires_at            DATETIME NOT NULL,
    external_subscription VARCHAR(255),
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY fk_sub_company (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY fk_sub_plan    (plan_id)    REFERENCES plans(id)    ON DELETE SET NULL,
    INDEX idx_sub_company (company_id),
    INDEX idx_sub_status  (status)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 1.6. Company runtime settings
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS company_settings (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id  INT UNSIGNED NOT NULL,
    key_name    VARCHAR(100) NOT NULL,
    value       VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY fk_setting_company (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE KEY uq_company_key (company_id, key_name)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 2. Users  (Admins / HR / CHRO)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id    INT UNSIGNED NOT NULL,
    username      VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email         VARCHAR(150) NOT NULL,
    full_name     VARCHAR(200) NOT NULL,
    role          VARCHAR(50) NOT NULL DEFAULT 'HR',
    is_active     TINYINT(1)  NOT NULL DEFAULT 1,
    last_login    DATETIME    NULL,
    created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE  KEY uq_username_company (company_id, username),
    UNIQUE  KEY uq_email_company     (company_id, email),
    FOREIGN KEY fk_user_company      (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    INDEX   idx_user_company         (company_id),
    INDEX   idx_user_role            (role)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 3. Departments
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id  INT UNSIGNED NOT NULL,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY fk_dept_company (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    INDEX idx_dept_company (company_id)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 4. Employees Core
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees_core (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id              INT UNSIGNED NOT NULL,
    employee_code           VARCHAR(50)  NOT NULL,
    first_name              VARCHAR(100) NOT NULL,
    last_name               VARCHAR(100) NOT NULL,
    email                   VARCHAR(150) NOT NULL,
    phone                   VARCHAR(30),
    department_id           INT UNSIGNED NULL,
    job_title               VARCHAR(150),
    employment_type         ENUM('Full-Time','Part-Time','Contract','Intern') DEFAULT 'Full-Time',
    status                  ENUM('Active','Inactive','Terminated','On Leave')  DEFAULT 'Active',
    hire_date               DATE NOT NULL,
    termination_date        DATE NULL,
    date_of_birth           DATE NULL,
    gender                  ENUM('Male','Female','Other','Prefer not to say') DEFAULT 'Prefer not to say',
    nationality             VARCHAR(100),
    address                 TEXT,
    emergency_contact_name  VARCHAR(200),
    emergency_contact_phone VARCHAR(30),
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE  KEY uq_emp_code_company (company_id, employee_code),
    FOREIGN KEY fk_emp_company      (company_id)   REFERENCES companies(id)   ON DELETE CASCADE,
    FOREIGN KEY fk_emp_department   (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    INDEX idx_emp_company    (company_id),
    INDEX idx_emp_status     (status),
    INDEX idx_emp_department (department_id),
    INDEX idx_emp_hire_date  (hire_date)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 5. Attendance
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id    INT UNSIGNED NOT NULL,
    employee_id   INT UNSIGNED NOT NULL,
    work_date     DATE         NOT NULL,
    check_in      TIME         NULL,
    check_out     TIME         NULL,
    status        ENUM('Present','Absent','Late','Half-Day','Work From Home','Holiday') DEFAULT 'Present',
    working_hours DECIMAL(5,2) NULL,
    notes         VARCHAR(500),
    recorded_by   INT UNSIGNED NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE  KEY uq_attendance            (company_id, employee_id, work_date),
    FOREIGN KEY fk_att_company           (company_id)  REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_att_employee          (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE,
    FOREIGN KEY fk_att_recorder         (recorded_by) REFERENCES users(id)          ON DELETE SET NULL,
    INDEX idx_att_date     (work_date),
    INDEX idx_att_employee (employee_id),
    INDEX idx_att_status   (status)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 6. Leave Balances
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_balances (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id      INT UNSIGNED NOT NULL,
    employee_id     INT UNSIGNED NOT NULL,
    year            YEAR         NOT NULL,
    annual_total    INT NOT NULL DEFAULT 21,
    annual_used     INT NOT NULL DEFAULT 0,
    sick_total      INT NOT NULL DEFAULT 14,
    sick_used       INT NOT NULL DEFAULT 0,
    emergency_total INT NOT NULL DEFAULT 5,
    emergency_used  INT NOT NULL DEFAULT 0,
    other_used      INT NOT NULL DEFAULT 0,
    UNIQUE  KEY uq_balance_year  (company_id, employee_id, year),
    FOREIGN KEY fk_bal_company   (company_id)  REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_bal_employee  (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE,
    INDEX idx_balance_employee (employee_id)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 7. Leave Requests
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_requests (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id      INT UNSIGNED NOT NULL,
    employee_id     INT UNSIGNED NOT NULL,
    leave_type      ENUM('Annual','Sick','Emergency','Maternity','Paternity','Unpaid','Other') NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    days_requested  INT  NOT NULL,
    reason          TEXT,
    status          ENUM('Pending','Approved','Rejected','Cancelled') DEFAULT 'Pending',
    reviewed_by     INT UNSIGNED NULL,
    reviewed_at     DATETIME NULL,
    review_notes    TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY fk_leave_company   (company_id)  REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_leave_employee  (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE,
    FOREIGN KEY fk_leave_reviewer  (reviewed_by) REFERENCES users(id)          ON DELETE SET NULL,
    INDEX idx_leave_employee  (employee_id),
    INDEX idx_leave_status    (status),
    INDEX idx_leave_dates     (start_date, end_date)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 8. Compensation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compensation (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id          INT UNSIGNED    NOT NULL,
    employee_id         INT UNSIGNED    NOT NULL,
    basic_salary        DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    housing_allowance   DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    transport_allowance DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    meal_allowance      DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    other_allowances    DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    income_tax_rate     DECIMAL(5,2)    NOT NULL DEFAULT 15.00  COMMENT 'Percentage e.g. 15 = 15%',
    social_insurance    DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    health_insurance    DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    other_deductions    DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    currency            CHAR(3)         NOT NULL DEFAULT 'USD',
    effective_date      DATE            NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY fk_comp_company  (company_id)  REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_comp_employee (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE,
    INDEX idx_comp_employee  (employee_id),
    INDEX idx_comp_effective (effective_date)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 9. Payroll Runs
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payroll_runs (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id        INT UNSIGNED  NOT NULL,
    employee_id       INT UNSIGNED  NOT NULL,
    pay_period        VARCHAR(7)    NOT NULL COMMENT 'Format: YYYY-MM',
    basic_salary      DECIMAL(15,2) NOT NULL,
    total_allowances  DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    gross_salary      DECIMAL(15,2) NOT NULL,
    bonus             DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    income_tax        DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_deductions  DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    net_salary        DECIMAL(15,2) NOT NULL,
    working_days      INT           NOT NULL DEFAULT 22,
    present_days      INT           NOT NULL DEFAULT 0,
    status            ENUM('Draft','Pending','Approved','Paid') NOT NULL DEFAULT 'Draft',
    processed_by      INT UNSIGNED  NULL,
    processed_at      DATETIME      NULL,
    notes             TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE  KEY uq_payroll          (company_id, employee_id, pay_period),
    FOREIGN KEY fk_pay_company      (company_id)   REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_pay_employee     (employee_id)  REFERENCES employees_core(id) ON DELETE CASCADE,
    FOREIGN KEY fk_pay_processor    (processed_by) REFERENCES users(id)          ON DELETE SET NULL,
    INDEX idx_payroll_period   (pay_period),
    INDEX idx_payroll_status   (status),
    INDEX idx_payroll_employee (employee_id)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────────────────────
-- 10. Performance Reviews
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS performance_reviews (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id       INT UNSIGNED NOT NULL,
    employee_id      INT UNSIGNED NOT NULL,
    reviewer_id      INT UNSIGNED NOT NULL,
    review_period    VARCHAR(50)  NOT NULL COMMENT 'e.g. Q1-2024, Annual-2024',
    review_date      DATE         NOT NULL,
    overall_rating   DECIMAL(3,1) NOT NULL COMMENT 'Scale 1.0 - 5.0',
    goals_score      DECIMAL(3,1) NULL,
    communication    DECIMAL(3,1) NULL,
    teamwork         DECIMAL(3,1) NULL,
    technical_skills DECIMAL(3,1) NULL,
    leadership       DECIMAL(3,1) NULL,
    strengths        TEXT,
    improvements     TEXT,
    comments         TEXT,
    status           ENUM('Draft','Submitted','Acknowledged') NOT NULL DEFAULT 'Draft',
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY fk_perf_company   (company_id)  REFERENCES companies(id)      ON DELETE CASCADE,
    FOREIGN KEY fk_perf_employee  (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE,
    FOREIGN KEY fk_perf_reviewer  (reviewer_id) REFERENCES users(id)          ON DELETE CASCADE,
    INDEX idx_perf_employee (employee_id),
    INDEX idx_perf_period   (review_period),
    INDEX idx_perf_date     (review_date)
) ENGINE=InnoDB;