-- Add missing columns to company_subscriptions table
-- Migration: add_subscription_custom_fields.sql (MySQL Version)

-- Add custom_price column (DECIMAL for pricing)
ALTER TABLE company_subscriptions ADD COLUMN custom_price DECIMAL(10, 2) DEFAULT NULL;

-- Add is_global_free column (TINYINT for MySQL boolean)
ALTER TABLE company_subscriptions ADD COLUMN is_global_free TINYINT(1) DEFAULT 0;

-- Add free_access_until column (DATE for trial expiration)
ALTER TABLE company_subscriptions ADD COLUMN free_access_until DATE DEFAULT NULL;