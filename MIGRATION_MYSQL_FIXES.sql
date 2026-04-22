-- ============================================================
-- HR Management System - MySQL Migration Script
-- Date: April 21, 2026
-- Purpose: Fix schema to match Python code and ensure MySQL compatibility
-- ============================================================

-- BACKUP INSTRUCTIONS:
-- Before running this migration, create a backup:
-- mysqldump -u root -p hr_system > backup_before_migration.sql

-- ============================================================
-- MIGRATION STEPS
-- ============================================================

-- Step 1: Fix Users table - Change email constraint to compound key
-- This allows multi-tenant email isolation (same email in different companies)
ALTER TABLE users DROP INDEX unique_email;
ALTER TABLE users ADD UNIQUE KEY unique_email (company_id, email);

-- Step 2: Add review fields to leave_requests table
-- These fields track who approved/rejected the leave and notes
ALTER TABLE leave_requests 
ADD COLUMN reason LONGTEXT NULL AFTER days_requested,
ADD COLUMN reviewed_by INT UNSIGNED NULL AFTER status,
ADD COLUMN reviewed_at TIMESTAMP NULL AFTER reviewed_by,
ADD COLUMN review_notes LONGTEXT NULL AFTER reviewed_at,
ADD FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL;

-- Step 3: Add indexes to foreign keys in leave_requests for query performance
ALTER TABLE leave_requests
ADD FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE IF NOT EXISTS,
ADD FOREIGN KEY (employee_id) REFERENCES employees_core(id) ON DELETE CASCADE IF NOT EXISTS;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Verify users table changes
SELECT CONSTRAINT_NAME, UNIQUE_CONSTRAINT_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'users' AND CONSTRAINT_NAME LIKE '%email%';

-- Verify leave_requests new columns exist
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'leave_requests' 
AND COLUMN_NAME IN ('reviewed_by', 'reviewed_at', 'review_notes', 'reason')
ORDER BY ORDINAL_POSITION;

-- Verify foreign keys on leave_requests
SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'leave_requests' AND REFERENCED_TABLE_NAME IS NOT NULL;

-- ============================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================
/*
ALTER TABLE users DROP INDEX unique_email;
ALTER TABLE users ADD UNIQUE KEY unique_email (email);

ALTER TABLE leave_requests DROP COLUMN reason;
ALTER TABLE leave_requests DROP COLUMN reviewed_by;
ALTER TABLE leave_requests DROP COLUMN reviewed_at;
ALTER TABLE leave_requests DROP COLUMN review_notes;
*/

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
