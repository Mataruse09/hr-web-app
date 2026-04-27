"""
Subscription Model - Manages subscription plans and feature access
"""
from models.db import query, mutate
from datetime import datetime, date
import logging
import traceback

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION PLANS
# ═══════════════════════════════════════════════════════════════════════════

def get_all_plans():
    """Get all active subscription plans."""
    return query(
        "SELECT * FROM subscription_plans WHERE is_active = TRUE ORDER BY price_monthly",
    )


def get_plan_by_id(plan_id: int):
    """Get a specific subscription plan by ID."""
    return query(
        "SELECT * FROM subscription_plans WHERE id = %s",
        (plan_id,), one=True
    )


def get_plan_by_name(name: str):
    """Get a specific subscription plan by name."""
    return query(
        "SELECT * FROM subscription_plans WHERE name = %s",
        (name,), one=True
    )


# ═══════════════════════════════════════════════════════════════════════════
# COMPANY SUBSCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_company_subscription(company_id: int):
    """Get the active subscription for a company."""
    try:
        return query(
            """SELECT cs.*, sp.name as plan_name, sp.display_name as plan_display_name,
                      sp.price_monthly, sp.price_yearly, sp.max_employees, sp.max_users, sp.features,
                      cs.custom_price, cs.is_global_free, cs.free_access_until
               FROM company_subscriptions cs
               JOIN subscription_plans sp ON cs.plan_id = sp.id
               WHERE cs.company_id = %s AND cs.status IN ('active', 'trial')
               ORDER BY cs.created_at DESC
               LIMIT 1""",
            (company_id,), one=True
        )
    except Exception as e:
        logger.error(f"Error getting company subscription: {e}")
        logger.error(traceback.format_exc())
        return None


def create_company_subscription(company_id: int, plan_id: int, start_date: date, 
                                end_date: date = None, status: str = 'trial',
                                auto_renew: bool = True):
    """Create a new subscription for a company."""
    return mutate(
        """INSERT INTO company_subscriptions 
           (company_id, plan_id, status, start_date, end_date, auto_renew) 
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (company_id, plan_id, status, start_date, end_date, auto_renew)
    )


def update_subscription_status(company_id: int, status: str):
    """Update the subscription status for a company."""
    mutate(
        "UPDATE company_subscriptions SET status = %s, updated_at = %s WHERE company_id = %s",
        (status, datetime.utcnow(), company_id)
    )


def cancel_subscription(company_id: int, cancel_at_period_end: bool = True):
    """Cancel a company's subscription."""
    mutate(
        """UPDATE company_subscriptions 
           SET cancel_at_period_end = %s, auto_renew = FALSE, updated_at = %s 
           WHERE company_id = %s AND status IN ('active', 'trial')""",
        (cancel_at_period_end, datetime.utcnow(), company_id)
    )


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE ACCESS
# ═══════════════════════════════════════════════════════════════════════════

def get_all_features():
    """Get all subscription features."""
    return query(
        "SELECT * FROM subscription_features ORDER BY category, display_name",
    )


def get_feature_by_name(name: str):
    """Get a specific feature by name."""
    return query(
        "SELECT * FROM subscription_features WHERE name = %s",
        (name,), one=True
    )


def has_feature(company_id: int, feature_name: str) -> bool:
    """
    Check if a company has access to a specific feature.
    Returns True if the feature is available for the company's subscription.
    """
    try:
        # Get company's active subscription
        subscription = get_company_subscription(company_id)
        
        if not subscription:
            # No subscription - check if feature is in free plan
            free_plan = get_plan_by_name('free')
            if free_plan:
                features = free_plan.get('features', [])
                return feature_name in features
            return False
        
        # Check if feature is in the plan's features
        features = subscription.get('features', [])
        if isinstance(features, str):
            import json
            features = json.loads(features)
        
        return feature_name in features
    except Exception as e:
        logger.error(f"Error checking feature {feature_name}: {e}")
        logger.error(traceback.format_exc())
        # Default to True on error to prevent blocking access
        return True


def get_company_features(company_id: int) -> list:
    """Get all features available to a company."""
    subscription = get_company_subscription(company_id)
    
    if not subscription:
        free_plan = get_plan_by_name('free')
        if free_plan:
            features = free_plan.get('features', [])
            if isinstance(features, str):
                import json
                features = json.loads(features)
            return features
        return []
    
    features = subscription.get('features', [])
    if isinstance(features, str):
        import json
        features = json.loads(features)
    return features


def can_access_ai(company_id: int) -> bool:
    """Check if company can access AI features."""
    return has_feature(company_id, 'ai_analytics')


def can_access_forecasting(company_id: int) -> bool:
    """Check if company can access forecasting features."""
    return has_feature(company_id, 'forecasting')


def can_access_gamification(company_id: int) -> bool:
    """Check if company can access gamification features."""
    return has_feature(company_id, 'gamification')


def can_access_compliance(company_id: int) -> bool:
    """Check if company can access compliance features."""
    return has_feature(company_id, 'compliance')


def can_access_payroll(company_id: int) -> bool:
    """Check if company can access payroll features."""
    return has_feature(company_id, 'payroll')


def can_access_appraisals(company_id: int) -> bool:
    """Check if company can access appraisal features."""
    return has_feature(company_id, 'appraisals')


# ═══════════════════════════════════════════════════════════════════════════
# COMPANY UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_subscription_status(company_id: int) -> dict:
    """Get detailed subscription status for a company."""
    try:
        subscription = get_company_subscription(company_id)
        
        if not subscription:
            return {
                'status': 'none',
                'plan_name': 'None',
                'is_active': False,
                'features': []
            }
        
        features = subscription.get('features', [])
        if isinstance(features, str):
            import json
            features = json.loads(features)
        
        return {
            'status': subscription.get('status'),
            'plan_name': subscription.get('plan_name'),
            'plan_display_name': subscription.get('plan_display_name'),
            'start_date': subscription.get('start_date'),
            'end_date': subscription.get('end_date'),
            'auto_renew': subscription.get('auto_renew'),
            'is_active': subscription.get('status') in ('active', 'trial'),
            'features': features,
            'max_employees': subscription.get('max_employees'),
            'max_users': subscription.get('max_users')
        }
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        logger.error(traceback.format_exc())
        # Return default active status on error to prevent blocking access
        return {
            'status': 'active',
            'plan_name': 'Free',
            'plan_display_name': 'Free Plan',
            'is_active': True,
            'features': []
        }


def check_employee_limit(company_id: int) -> tuple:
    """
    Check if company has reached employee limit.
    Returns (can_add, current_count, max_count, message)
    """
    subscription = get_company_subscription(company_id)
    
    if not subscription:
        free_plan = get_plan_by_name('free')
        max_employees = free_plan.get('max_employees', 10) if free_plan else 10
    else:
        max_employees = subscription.get('max_employees', 10)
    
    # Get current employee count
    from models.employee_model import count_employees
    current_count = count_employees(company_id)
    
    can_add = current_count < max_employees
    message = f"Employee limit: {current_count}/{max_employees}"
    
    return can_add, current_count, max_employees, message