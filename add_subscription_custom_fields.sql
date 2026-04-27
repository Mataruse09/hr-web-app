-- Add missing columns to company_subscriptions table
-- Migration: add_subscription_custom_fields.sql

-- Add custom_price column (DECIMAL for pricing)
ALTER TABLE company_subscriptions ADD COLUMN custom_price DECIMAL(10, 2) DEFAULT NULL;

-- Add is_global_free column (BOOLEAN for global free access)
ALTER TABLE company_subscriptions ADD COLUMN is_global_free BOOLEAN DEFAULT FALSE;

-- Add free_access_until column (DATE for trial expiration)
ALTER TABLE company_subscriptions ADD COLUMN free_access_until DATE DEFAULT NULL;