-- Add missing columns to company_subscriptions table
-- This migration adds subscription management columns that may be missing

-- Add is_global_free column if not exists
ALTER TABLE company_subscriptions ADD COLUMN is_global_free TINYINT(1) DEFAULT 0;

-- Add free_access_until column if not exists
ALTER TABLE company_subscriptions ADD COLUMN free_access_until DATE DEFAULT NULL;

-- Add custom_price column if not exists
ALTER TABLE company_subscriptions ADD COLUMN custom_price DECIMAL(10, 2) DEFAULT NULL;

-- Add is_featured column to subscription_plans if not exists
ALTER TABLE subscription_plans ADD COLUMN is_featured TINYINT(1) DEFAULT 0;

SELECT 'Subscription columns migration completed!' as result;