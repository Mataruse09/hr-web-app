-- Add payment_method column to company_subscriptions
ALTER TABLE company_subscriptions 
ADD COLUMN payment_method VARCHAR(50);

-- Update existing records
UPDATE company_subscriptions SET payment_method = 'card' WHERE payment_method IS NULL;

-- Make sure the column has a default
ALTER TABLE company_subscriptions ALTER COLUMN payment_method SET DEFAULT 'card';