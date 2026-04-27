"""
Subscription Service - Feature gating and access control
"""
from functools import wraps
from flask import flash, redirect, url_for, session, render_template
import logging

from models.subscription_model import (
    has_feature,
    get_company_features,
    get_subscription_status,
    can_access_ai,
    can_access_forecasting,
    can_access_gamification,
    can_access_compliance,
    can_access_payroll,
    can_access_appraisals,
    get_company_subscription,
    get_all_plans,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE TO PLAN MAPPING - Dynamically determined from database
# ═══════════════════════════════════════════════════════════════════════════

def get_feature_required_plan(feature_name: str) -> str:
    """
    Dynamically determine which plan is required for a feature.
    This reads from the database to find the minimum plan that includes the feature.
    """
    plans = get_all_plans()
    
    # Define feature requirements based on the subscription_migration.sql
    # Features are included in plans in this order: free -> starter -> professional -> enterprise
    feature_plan_requirements = {
        # Basic features (Free plan)
        'employees': 'Free',
        'attendance': 'Free',
        'leave': 'Free',
        'basic_reports': 'Free',
        
        # Advanced features (Starter plan)
        'payroll': 'Starter',
        'appraisals': 'Starter',
        
        # AI features (Professional plan)
        'ai_analytics': 'Professional',
        'forecasting': 'Professional',
        'attrition': 'Professional',
        
        # Premium features (Enterprise plan)
        'compliance': 'Enterprise',
        'gamification': 'Enterprise',
        'advanced_forecasting': 'Enterprise',
    }
    
    return feature_plan_requirements.get(feature_name, 'Professional')


# ═══════════════════════════════════════════════════════════════════════════
# DECORATORS FOR FEATURE GATING
# ═══════════════════════════════════════════════════════════════════════════

def subscription_required(feature_name: str):
    """
    Decorator to check if the company has access to a specific feature.
    Usage: @subscription_required('ai_analytics')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            company_id = session.get('company_id')
            
            if not company_id:
                flash('Please log in to access this feature.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if feature is available
            if not has_feature(company_id, feature_name):
                # Get subscription status for the upgrade message
                sub_status = get_subscription_status(company_id)
                plan_name = sub_status.get('plan_display_name', 'Current Plan')
                
                flash(
                    f'This feature is not available on your {plan_name} plan. '
                    f'Please upgrade to access this feature.',
                    'warning'
                )
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def ai_feature_required(f):
    """
    Decorator specifically for AI features.
    Now dynamically determines the required plan from the database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        company_id = session.get('company_id')
        
        if not company_id:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not can_access_ai(company_id):
            # Dynamically determine the required plan
            required_plan = get_feature_required_plan('ai_analytics')
            # Render upgrade page instead of redirecting
            return render_upgrade_page('AI Analytics', required_plan, 'ai_analytics')
        
        return f(*args, **kwargs)
    return decorated_function


def render_upgrade_page(feature_name: str, required_plan: str, feature_key: str):
    """
    Render an upgrade required page instead of redirecting.
    This allows the feature to remain visible in navigation but be disabled.
    
    Now dynamically determines the required plan based on the feature.
    """
    from flask import render_template
    company_id = session.get('company_id')
    sub_status = get_subscription_status(company_id)
    current_plan = sub_status.get('plan_display_name', 'Free') if sub_status else 'Free'
    current_plan_name = sub_status.get('plan_name', 'free') if sub_status else 'free'
    
    # Dynamically determine the required plan if not provided
    if feature_key and required_plan == 'Unknown':
        required_plan = get_feature_required_plan(feature_key)
    
    # Generate a more accurate message based on current plan
    upgrade_message = _generate_upgrade_message(current_plan, current_plan_name, required_plan, feature_name)
    
    return render_template(
        'upgrade_required.html',
        feature_name=feature_name,
        required_plan=required_plan,
        current_plan=current_plan,
        current_plan_name=current_plan_name,
        feature_key=feature_key,
        upgrade_message=upgrade_message
    )


def _generate_upgrade_message(current_plan: str, current_plan_name: str, required_plan: str, feature_name: str) -> str:
    """
    Generate an accurate upgrade message based on the user's current plan.
    """
    # Plan hierarchy for comparison
    plan_hierarchy = {'free': 0, 'starter': 1, 'professional': 2, 'enterprise': 3}
    
    current_level = plan_hierarchy.get(current_plan_name.lower(), 0)
    required_level = plan_hierarchy.get(required_plan.lower(), 2)
    
    if current_level >= required_level:
        # User has the required plan but feature might not be enabled - could be a billing issue
        return f"You have the {current_plan} plan, but access to {feature_name} is not enabled. Please contact support or verify your subscription is active."
    else:
        # User needs to upgrade
        return f"The {feature_name} feature requires a {required_plan} subscription plan. Your current plan is {current_plan}. Please upgrade to access this feature."


def forecasting_feature_required(f):
    """
    Decorator specifically for Forecasting features.
    Now dynamically determines the required plan from the database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        company_id = session.get('company_id')
        
        if not company_id:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not can_access_forecasting(company_id):
            # Dynamically determine the required plan
            required_plan = get_feature_required_plan('forecasting')
            # Render upgrade page instead of redirecting
            return render_upgrade_page('Labour Forecasting', required_plan, 'forecasting')
        
        return f(*args, **kwargs)
    return decorated_function


def gamification_feature_required(f):
    """
    Decorator specifically for Gamification features.
    Now dynamically determines the required plan from the database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        company_id = session.get('company_id')
        
        if not company_id:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not can_access_gamification(company_id):
            # Dynamically determine the required plan
            required_plan = get_feature_required_plan('gamification')
            # Render upgrade page instead of redirecting
            return render_upgrade_page('Gamification', required_plan, 'gamification')
        
        return f(*args, **kwargs)
    return decorated_function


def compliance_feature_required(f):
    """
    Decorator specifically for Compliance features.
    Now dynamically determines the required plan from the database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        company_id = session.get('company_id')
        
        if not company_id:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not can_access_compliance(company_id):
            # Dynamically determine the required plan
            required_plan = get_feature_required_plan('compliance')
            # Render upgrade page instead of redirecting
            return render_upgrade_page('Compliance Management', required_plan, 'compliance')
        
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE CONTEXT HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def add_subscription_context():
    """
    Add subscription context to Flask's g object for template access.
    Call this in before_request in app.py
    """
    from flask import g, session
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    company_id = session.get('company_id')
    if company_id:
        try:
            g.subscription = get_subscription_status(company_id)
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            g.subscription = {'status': 'active', 'plan_name': 'Free', 'features': [], 'is_active': True}
        
        try:
            g.features = get_company_features(company_id)
        except Exception as e:
            logger.error(f"Error getting company features: {e}")
            g.features = []
        
        try:
            g.can_access_ai = can_access_ai(company_id)
        except Exception as e:
            logger.error(f"Error checking AI access: {e}")
            g.can_access_ai = True  # Default to True on error
        
        try:
            g.can_access_forecasting = can_access_forecasting(company_id)
        except Exception as e:
            logger.error(f"Error checking forecasting access: {e}")
            g.can_access_forecasting = True
        
        try:
            g.can_access_gamification = can_access_gamification(company_id)
        except Exception as e:
            logger.error(f"Error checking gamification access: {e}")
            g.can_access_gamification = True
        
        try:
            g.can_access_compliance = can_access_compliance(company_id)
        except Exception as e:
            logger.error(f"Error checking compliance access: {e}")
            g.can_access_compliance = True
        
        try:
            g.can_access_payroll = can_access_payroll(company_id)
        except Exception as e:
            logger.error(f"Error checking payroll access: {e}")
            g.can_access_payroll = True
        
        try:
            g.can_access_appraisals = can_access_appraisals(company_id)
        except Exception as e:
            logger.error(f"Error checking appraisals access: {e}")
            g.can_access_appraisals = True
    else:
        g.subscription = {'status': 'none', 'plan_name': 'Free', 'features': []}
        g.features = []
        g.can_access_ai = False
        g.can_access_forecasting = False
        g.can_access_gamification = False
        g.can_access_compliance = False
        g.can_access_payroll = False
        g.can_access_appraisals = False


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE AVAILABILITY CHECKS FOR TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════

def is_feature_available(company_id: int, feature: str) -> bool:
    """Check if a feature is available for a company."""
    return has_feature(company_id, feature)


def get_available_features(company_id: int) -> list:
    """Get list of available features for a company."""
    return get_company_features(company_id)


def get_upgrade_message(current_plan: str, required_plan: str) -> str:
    """Generate upgrade message for users."""
    return (
        f'The {required_plan} features require a higher subscription plan. '
        f'Your current plan: {current_plan}. '
        f'Please upgrade to access this feature.'
    )


def get_all_features_with_status(company_id: int) -> list:
    """
    Get all subscription features with their availability status.
    Returns list of dicts with feature info and whether it's enabled.
    """
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        from models.subscription_model import get_all_features, has_feature
        
        all_features = get_all_features()
        available_features = get_company_features(company_id)
        
        result = []
        for feature in all_features:
            try:
                is_available = has_feature(company_id, feature['name'])
            except Exception as e:
                logger.error(f"Error checking feature {feature.get('name')}: {e}")
                is_available = True  # Default to True on error
            
            result.append({
                'id': feature.get('id'),
                'name': feature.get('name'),
                'display_name': feature.get('display_name'),
                'description': feature.get('description'),
                'category': feature.get('category'),
                'required_plan': feature.get('required_plan', 'Professional'),
                'is_available': is_available
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting all features with status: {e}")
        logger.error(traceback.format_exc())
        return []


def get_disabled_features(company_id: int) -> list:
    """Get list of features that are disabled for a company."""
    all_features = get_all_features_with_status(company_id)
    return [f for f in all_features if not f['is_available']]