-- Add missing columns to compensation table
-- This migration adds all compensation settings fields

ALTER TABLE compensation ADD COLUMN effective_date DATE DEFAULT NULL;
ALTER TABLE compensation ADD COLUMN housing_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN transport_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN meal_allowance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN other_allowances DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN income_tax_rate DECIMAL(5,2) DEFAULT 15.00;
ALTER TABLE compensation ADD COLUMN social_insurance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN health_insurance DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN other_deductions DECIMAL(15,2) DEFAULT 0;
ALTER TABLE compensation ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;