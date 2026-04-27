-- Add gender column to employees_core table
ALTER TABLE employees_core ADD COLUMN gender VARCHAR(50) DEFAULT 'Prefer not to say';

-- Verify the column was added
-- DESCRIBE employees_core;