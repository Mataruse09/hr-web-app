-- Add ban system columns to companies table (MySQL)
-- Run this to add the missing columns for the owner dashboard

-- Add is_banned column if it doesn't exist
ALTER TABLE companies ADD COLUMN is_banned TINYINT(1) DEFAULT 0;

-- Add ban_reason column if it doesn't exist
ALTER TABLE companies ADD COLUMN ban_reason TEXT;

-- Add banned_at column if it doesn't exist
ALTER TABLE companies ADD COLUMN banned_at TIMESTAMP NULL;

-- Add banned_by column if it doesn't exist
ALTER TABLE companies ADD COLUMN banned_by INT UNSIGNED NULL;

-- Add ban_type column if it doesn't exist
ALTER TABLE companies ADD COLUMN ban_type VARCHAR(20) DEFAULT 'manual';

-- Add auto_ban_trigger column if it doesn't exist
ALTER TABLE companies ADD COLUMN auto_ban_trigger VARCHAR(50);

-- Add terms acceptance columns if they don't exist
ALTER TABLE companies ADD COLUMN terms_accepted TINYINT(1) DEFAULT 0;
ALTER TABLE companies ADD COLUMN terms_accepted_at TIMESTAMP NULL;
ALTER TABLE companies ADD COLUMN terms_version VARCHAR(20);

-- Add custom pricing columns to company_subscriptions if they don't exist
ALTER TABLE company_subscriptions ADD COLUMN custom_price DECIMAL(10,2) NULL;
ALTER TABLE company_subscriptions ADD COLUMN is_global_free TINYINT(1) DEFAULT 0;
ALTER TABLE company_subscriptions ADD COLUMN free_access_until TIMESTAMP NULL;

-- Add is_featured column to subscription_plans if it doesn't exist
ALTER TABLE subscription_plans ADD COLUMN is_featured TINYINT(1) DEFAULT 0;