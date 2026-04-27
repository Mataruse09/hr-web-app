"""
Run Subscription Migration
Execute the subscription system database migration
"""
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.db import mutate, query

def run_migration():
    print("=" * 60)
    print("Running Subscription System Migration")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Check if tables already exist
        try:
            existing = query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('subscription_plans', 'company_subscriptions', 'subscription_features')
            """)
            
            if existing and len(existing) >= 3:
                print("\n✓ Subscription tables already exist!")
                print("  - subscription_plans")
                print("  - company_subscriptions") 
                print("  - subscription_features")
                return True
        except Exception as e:
            print(f"Note: {e}")
        
        # Create subscription_plans table
        print("\n1. Creating subscription_plans table...")
        try:
            mutate("""
                CREATE TABLE IF NOT EXISTS subscription_plans (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    display_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    price_yearly DECIMAL(10, 2),
                    max_employees INTEGER NOT NULL DEFAULT 10,
                    max_users INTEGER NOT NULL DEFAULT 5,
                    features JSONB NOT NULL DEFAULT '[]',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_trial BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Create company_subscriptions table
        print("\n2. Creating company_subscriptions table...")
        try:
            mutate("""
                CREATE TABLE IF NOT EXISTS company_subscriptions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    start_date DATE NOT NULL,
                    end_date DATE,
                    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
                    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
                    stripe_customer_id VARCHAR(255),
                    stripe_subscription_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Create subscription_features table
        print("\n3. Creating subscription_features table...")
        try:
            mutate("""
                CREATE TABLE IF NOT EXISTS subscription_features (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    display_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    category VARCHAR(50) NOT NULL,
                    is_premium BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Insert default subscription plans
        print("\n4. Inserting default subscription plans...")
        try:
            mutate("""
                INSERT INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_employees, max_users, features, is_active, is_trial) VALUES
                ('free', 'Free Plan', 'Basic HR features for small teams', 0, 0, 10, 3, '["employees", "attendance", "leave", "basic_reports"]', true, false),
                ('starter', 'Starter Plan', 'Essential HR features for growing teams', 29.99, 299.99, 50, 10, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals"]', true, false),
                ('professional', 'Professional Plan', 'Advanced HR with AI analytics', 79.99, 799.99, 200, 25, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition"]', true, false),
                ('enterprise', 'Enterprise Plan', 'Full-featured HR for large organizations', 199.99, 1999.99, 1000, 100, '["employees", "attendance", "leave", "basic_reports", "payroll", "appraisals", "ai_analytics", "forecasting", "attrition", "compliance", "gamification", "advanced_forecasting"]', true, false)
                ON CONFLICT (name) DO NOTHING
            """)
            print("   ✓ Inserted default plans")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Insert subscription features
        print("\n5. Inserting subscription features...")
        try:
            mutate("""
                INSERT INTO subscription_features (name, display_name, description, category, is_premium) VALUES
                ('employees', 'Employee Management', 'Basic employee CRUD operations', 'basic', false),
                ('attendance', 'Attendance Tracking', 'Track employee attendance and hours', 'basic', false),
                ('leave', 'Leave Management', 'Manage employee leave requests', 'basic', false),
                ('basic_reports', 'Basic Reports', 'Standard HR reports and dashboards', 'basic', false),
                ('payroll', 'Payroll', 'Payroll processing and management', 'advanced', true),
                ('appraisals', 'Appraisals', 'Performance appraisal system', 'advanced', true),
                ('ai_analytics', 'AI Analytics', 'AI-powered workforce insights', 'ai', true),
                ('forecasting', 'Labour Forecasting', 'Workforce demand forecasting', 'ai', true),
                ('attrition', 'Attrition Analysis', 'Employee attrition risk analysis', 'ai', true),
                ('compliance', 'Compliance Management', 'Regulatory compliance tracking', 'premium', true),
                ('gamification', 'Gamification', 'Employee engagement and rewards', 'premium', true),
                ('advanced_forecasting', 'Advanced Forecasting', 'ML-powered workforce predictions', 'ai', true)
                ON CONFLICT (name) DO NOTHING
            """)
            print("   ✓ Inserted default features")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Add columns to companies table
        print("\n6. Adding columns to companies table...")
        try:
            mutate("""
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'trial'
            """)
            print("   ✓ Added subscription_status")
        except Exception as e:
            print(f"   Note: {e}")
        
        try:
            mutate("""
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS plan_id INTEGER REFERENCES subscription_plans(id)
            """)
            print("   ✓ Added plan_id")
        except Exception as e:
            print(f"   Note: {e}")
        
        try:
            mutate("""
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS subscription_start DATE
            """)
            print("   ✓ Added subscription_start")
        except Exception as e:
            print(f"   Note: {e}")
        
        try:
            mutate("""
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS subscription_end DATE
            """)
            print("   ✓ Added subscription_end")
        except Exception as e:
            print(f"   Note: {e}")
        
        # Create indexes
        print("\n7. Creating indexes...")
        try:
            mutate("CREATE INDEX IF NOT EXISTS idx_company_subscriptions_company ON company_subscriptions(company_id)")
            print("   ✓ Created company index")
        except Exception as e:
            print(f"   Note: {e}")
        
        try:
            mutate("CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status ON company_subscriptions(status)")
            print("   ✓ Created status index")
        except Exception as e:
            print(f"   Note: {e}")
        
        print("\n" + "=" * 60)
        print("✓ Subscription migration complete!")
        print("=" * 60)
        
        # Verify
        print("\nVerifying tables...")
        try:
            plans = query("SELECT name, display_name, price_monthly FROM subscription_plans ORDER BY price_monthly")
            print("\nSubscription Plans:")
            for p in plans:
                print(f"  - {p['display_name']}: ${p['price_monthly']}/month")
        except Exception as e:
            print(f"   Error verifying: {e}")
    
    return True

if __name__ == "__main__":
    run_migration()