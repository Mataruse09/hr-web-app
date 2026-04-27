"""
Subscription Routes - Manage subscription plans and billing
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime, date, timedelta

from utils import login_required, roles_required
from models.db import query, mutate
from models.subscription_model import (
    get_all_plans,
    get_plan_by_id,
    get_plan_by_name,
    get_company_subscription,
    create_company_subscription,
    update_subscription_status,
    cancel_subscription,
    get_subscription_status,
    get_all_features,
    has_feature,
    get_company_features,
)
from services.subscription_service import can_access_ai, can_access_forecasting, can_access_gamification, can_access_compliance
from services.email_service import send_subscription_confirmation_email, send_subscription_notification_to_owner

logger = logging.getLogger(__name__)

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/plans')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def list_plans():
    """List all available subscription plans."""
    try:
        plans = get_all_plans()
        features = get_all_features()
        
        # Get current subscription
        company_id = session.get('company_id')
        current_subscription = get_company_subscription(company_id)
        
        return render_template(
            'subscription/plans.html',
            plans=plans,
            features=features,
            current_subscription=current_subscription,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading plans.', 'danger')
        return redirect(url_for('dashboard.index'))


@subscription_bp.route('/manage')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def manage_subscription():
    """Manage current subscription."""
    try:
        company_id = session.get('company_id')
        
        # Get subscription status
        sub_status = get_subscription_status(company_id)
        
        # Get available plans
        plans = get_all_plans()
        
        # Get company features
        features = get_company_features(company_id)
        
        return render_template(
            'subscription/manage.html',
            subscription=sub_status,
            plans=plans,
            features=features,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading subscription.', 'danger')
        return redirect(url_for('dashboard.index'))


@subscription_bp.route('/upgrade', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def upgrade_plan():
    """Upgrade to a new subscription plan - redirect to payment for paid plans."""
    try:
        company_id = session.get('company_id')
        plan_id = request.form.get('plan_id', type=int)
        
        if not plan_id:
            flash('Please select a plan.', 'warning')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get the new plan
        new_plan = get_plan_by_id(plan_id)
        if not new_plan:
            flash('Invalid plan selected.', 'danger')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get current subscription
        current_sub = get_company_subscription(company_id)
        
        # Check if this is a free plan - grant immediate access
        plan_price = float(new_plan.get('price_monthly', 0))
        is_free_plan = plan_price == 0
        
        if is_free_plan:
            # Free plan - grant immediate access
            from models.company_model import get_by_id
            company = get_by_id(company_id)
            company_name = company['name'] if company else 'Your Company'
            admin_name = session.get('name', 'Admin')
            admin_email = session.get('email', '')
            
            _activate_subscription(company_id, plan_id, new_plan, current_sub, company_name, admin_name, admin_email)
            flash(f'Successfully subscribed to {new_plan["display_name"]} plan!', 'success')
            return redirect(url_for('subscription.manage_subscription'))
        else:
            # Paid plan - redirect to payment page
            return redirect(url_for('subscription.payment_page', plan_id=plan_id))
    
    except Exception as e:
        logger.exception(e)
        flash('Error upgrading plan.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


@subscription_bp.route('/payment/<int:plan_id>')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def payment_page(plan_id: int):
    """Show payment method selection page."""
    try:
        company_id = session.get('company_id')
        
        # Get the plan
        new_plan = get_plan_by_id(plan_id)
        if not new_plan:
            flash('Invalid plan selected.', 'danger')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get company info
        from models.company_model import get_by_id
        company = get_by_id(company_id)
        company_name = company['name'] if company else 'Your Company'
        
        # Get admin email
        admin_email = session.get('email', '')
        
        # Determine billing cycle
        billing_cycle = 'monthly'
        if new_plan.get('price_yearly') and float(new_plan.get('price_yearly', 0)) > 0:
            billing_cycle = 'yearly'
        
        return render_template(
            'subscription/payment.html',
            plan_id=plan_id,
            plan_name=new_plan['display_name'],
            plan_description=new_plan.get('description', ''),
            plan_price=new_plan['price_monthly'],
            billing_cycle=billing_cycle,
            company_id=company_id,
            company_name=company_name,
            admin_email=admin_email,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading payment page.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


@subscription_bp.route('/process-payment', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def process_payment():
    """Process payment and activate subscription."""
    try:
        company_id = session.get('company_id')
        plan_id = request.form.get('plan_id', type=int)
        payment_method = request.form.get('payment_method', 'card')
        
        if not plan_id:
            flash('Invalid plan.', 'danger')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get the plan
        new_plan = get_plan_by_id(plan_id)
        if not new_plan:
            flash('Invalid plan.', 'danger')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get company info
        from models.company_model import get_by_id
        company = get_by_id(company_id)
        company_name = company['name'] if company else 'Your Company'
        admin_name = session.get('name', 'Admin')
        admin_email = session.get('email', '')
        
        # Get current subscription
        current_sub = get_company_subscription(company_id)
        
        # Process based on payment method
        if payment_method == 'card':
            # Validate card details (in production, use payment processor)
            card_number = request.form.get('card_number', '')
            card_expiry = request.form.get('card_expiry', '')
            card_cvv = request.form.get('card_cvv', '')
            card_name = request.form.get('card_name', '')
            
            # Basic validation
            if not card_number or not card_expiry or not card_cvv or not card_name:
                flash('Please fill in all card details.', 'warning')
                return redirect(url_for('subscription.payment_page', plan_id=plan_id))
            
            # Simulate payment processing (in production, integrate with Stripe/PayPal)
            payment_success = _process_card_payment(card_number, card_expiry, card_cvv, new_plan)
            
        elif payment_method == 'bank':
            # Bank transfer - set to pending until confirmed
            payment_success = _process_bank_transfer(company_id, plan_id, new_plan)
        
        else:
            flash('Invalid payment method.', 'danger')
            return redirect(url_for('subscription.manage_subscription'))
        
        if payment_success:
            # Activate subscription
            _activate_subscription(company_id, plan_id, new_plan, current_sub, company_name, admin_name, admin_email)
            flash(f'Payment successful! You now have access to the {new_plan["display_name"]} plan.', 'success')
        else:
            # Payment failed
            flash('Payment failed. Please check your card details and try again.', 'danger')
            return redirect(url_for('subscription.payment_page', plan_id=plan_id))
        
        return redirect(url_for('subscription.manage_subscription'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error processing payment.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


def _process_card_payment(card_number: str, card_expiry: str, card_cvv: str, plan: dict) -> bool:
    """
    Process card payment.
    In production, this would integrate with Stripe, PayPal, or another payment processor.
    For now, we simulate successful payment for testing.
    """
    # Basic card number validation (for simulation)
    card_number = card_number.replace(' ', '').replace('-', '')
    
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # In production, you would:
    # 1. Send card details to payment processor (never store them locally)
    # 2. Get authorization
    # 3. Capture payment
    
    # For simulation, we'll accept any valid-looking card
    logger.info(f"Processing card payment for plan: {plan['display_name']}")
    return True


def _process_bank_transfer(company_id: int, plan_id: int, plan: dict) -> bool:
    """
    Process bank transfer.
    Sets subscription to pending until bank transfer is confirmed.
    """
    from datetime import datetime
    
    # Create pending subscription
    start_date = date.today()
    
    # Check if subscription exists
    existing = get_company_subscription(company_id)
    
    if existing:
        mutate(
            """UPDATE company_subscriptions 
               SET plan_id = %s, status = 'pending_payment', 
                   payment_method = 'bank_transfer', updated_at = %s 
               WHERE company_id = %s""",
            (plan_id, datetime.utcnow(), company_id)
        )
    else:
        create_company_subscription(
            company_id=company_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=None,
            status='pending_payment',
            auto_renew=True
        )
    
    # Log for admin to verify
    logger.info(f"Bank transfer initiated for company {company_id}, plan {plan_id}")
    
    # For bank transfer, we return True but subscription stays pending
    # until admin verifies the transfer
    return True


def _activate_subscription(company_id: int, plan_id: int, new_plan: dict, current_sub, company_name: str, admin_name: str, admin_email: str):
    """Activate subscription and grant immediate access."""
    from datetime import datetime
    
    if current_sub:
        # Update existing subscription
        mutate(
            """UPDATE company_subscriptions 
               SET plan_id = %s, status = 'active', updated_at = %s 
               WHERE company_id = %s""",
            (plan_id, datetime.utcnow(), company_id)
        )
        
        # Also update company table
        mutate(
            """UPDATE companies 
               SET plan_id = %s, subscription_status = 'active', 
                   subscription_start = %s, subscription_end = %s 
               WHERE id = %s""",
            (plan_id, date.today(), date.today() + timedelta(days=30), company_id)
        )
    else:
        # Create new subscription
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        create_company_subscription(
            company_id=company_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status='active',
            auto_renew=True
        )
        
        # Update company table
        mutate(
            """UPDATE companies 
               SET plan_id = %s, subscription_status = 'active', 
                   subscription_start = %s, subscription_end = %s 
               WHERE id = %s""",
            (plan_id, start_date, end_date, company_id)
        )
    
    # Send confirmation email to admin
    try:
        send_subscription_confirmation_email(
            admin_name, 
            admin_email, 
            company_name, 
            new_plan['display_name']
        )
    except Exception as e:
        logger.warning(f"Failed to send subscription confirmation email: {e}")
    
    # Send notification to owner
    try:
        send_subscription_notification_to_owner(
            admin_name,
            admin_email,
            company_name,
            new_plan['display_name']
        )
    except Exception as e:
        logger.warning(f"Failed to send owner notification email: {e}")


def _set_pending_payment(company_id: int, plan_id: int, new_plan: dict, current_sub, company_name: str, admin_name: str, admin_email: str):
    """Set subscription to pending payment status."""
    from datetime import datetime
    
    if current_sub:
        # Update existing subscription to pending
        mutate(
            """UPDATE company_subscriptions 
               SET plan_id = %s, status = 'pending_payment', updated_at = %s 
               WHERE company_id = %s""",
            (plan_id, datetime.utcnow(), company_id)
        )
    else:
        # Create new subscription with pending status
        start_date = date.today()
        
        create_company_subscription(
            company_id=company_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=None,
            status='pending_payment',
            auto_renew=True
        )


@subscription_bp.route('/verify-payment', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def verify_payment():
    """
    Verify payment and activate subscription.
    This endpoint should be called after payment processor confirms payment.
    """
    try:
        company_id = session.get('company_id')
        payment_token = request.form.get('payment_token', '')
        
        # In production, verify the payment token with payment processor
        # For now, we'll simulate payment verification
        
        # Get current subscription with pending status
        current_sub = query(
            """SELECT cs.*, sp.display_name as plan_display_name
               FROM company_subscriptions cs
               JOIN subscription_plans sp ON cs.plan_id = sp.id
               WHERE cs.company_id = %s AND cs.status = 'pending_payment'
               ORDER BY cs.created_at DESC
               LIMIT 1""",
            (company_id,), one=True
        )
        
        if not current_sub:
            flash('No pending payment found.', 'warning')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get company info
        from models.company_model import get_by_id
        company = get_by_id(company_id)
        company_name = company['name'] if company else 'Your Company'
        
        # Get admin info
        admin_name = session.get('name', 'Admin')
        admin_email = session.get('email', '')
        
        # Activate the subscription
        plan_id = current_sub['plan_id']
        new_plan = get_plan_by_id(plan_id)
        
        _activate_subscription(company_id, plan_id, new_plan, current_sub, company_name, admin_name, admin_email)
        
        flash(f'Payment verified! You now have access to the {new_plan["display_name"]} plan.', 'success')
        
        return redirect(url_for('subscription.manage_subscription'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error verifying payment.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


@subscription_bp.route('/simulate-payment', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def simulate_payment():
    """
    Simulate payment for testing purposes.
    In production, this would be replaced with real payment processor integration.
    """
    try:
        company_id = session.get('company_id')
        
        # Get current subscription with pending status
        current_sub = query(
            """SELECT cs.*, sp.display_name as plan_display_name
               FROM company_subscriptions cs
               JOIN subscription_plans sp ON cs.plan_id = sp.id
               WHERE cs.company_id = %s AND cs.status = 'pending_payment'
               ORDER BY cs.created_at DESC
               LIMIT 1""",
            (company_id,), one=True
        )
        
        if not current_sub:
            flash('No pending payment found.', 'warning')
            return redirect(url_for('subscription.manage_subscription'))
        
        # Get company info
        from models.company_model import get_by_id
        company = get_by_id(company_id)
        company_name = company['name'] if company else 'Your Company'
        
        # Get admin info
        admin_name = session.get('name', 'Admin')
        admin_email = session.get('email', '')
        
        # Activate the subscription
        plan_id = current_sub['plan_id']
        new_plan = get_plan_by_id(plan_id)
        
        _activate_subscription(company_id, plan_id, new_plan, current_sub, company_name, admin_name, admin_email)
        
        flash(f'Payment successful! You now have access to the {new_plan["display_name"]} plan.', 'success')
        
        return redirect(url_for('subscription.manage_subscription'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error processing payment.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


@subscription_bp.route('/cancel', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def cancel_sub():
    """Cancel the current subscription."""
    try:
        company_id = session.get('company_id')
        cancel_at_period_end = request.form.get('cancel_at_period_end', 'true').lower() == 'true'
        
        cancel_subscription(company_id, cancel_at_period_end)
        
        if cancel_at_period_end:
            flash('Your subscription will be cancelled at the end of the billing period.', 'info')
        else:
            flash('Your subscription has been cancelled.', 'info')
        
        return redirect(url_for('subscription.manage_subscription'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error cancelling subscription.', 'danger')
        return redirect(url_for('subscription.manage_subscription'))


@subscription_bp.route('/check-feature')
@login_required
def check_feature():
    """API endpoint to check if a feature is available."""
    company_id = session.get('company_id')
    feature = request.args.get('feature', '')
    
    if not feature:
        return jsonify({'success': False, 'error': 'Feature name required'}), 400
    
    has_access = has_feature(company_id, feature)
    
    return jsonify({
        'success': True,
        'feature': feature,
        'has_access': has_access,
    })


@subscription_bp.route('/status')
@login_required
def subscription_status():
    """API endpoint to get subscription status."""
    company_id = session.get('company_id')
    
    status = get_subscription_status(company_id)
    
    return jsonify({
        'success': True,
        'subscription': status,
    })


# ═══════════════════════════════════════════════════════════════════════════
# TRIAL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@subscription_bp.route('/start-trial', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def start_trial():
    """Start a free trial of premium features."""
    try:
        company_id = session.get('company_id')
        
        # Get professional plan for trial
        pro_plan = get_plan_by_name('professional')
        if not pro_plan:
            flash('Trial not available at this time.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Create trial subscription
        start_date = date.today()
        end_date = start_date + timedelta(days=14)  # 14-day trial
        
        # Check if already has subscription
        existing = get_company_subscription(company_id)
        if existing:
            # Update to trial
            mutate(
                """UPDATE company_subscriptions 
                   SET plan_id = %s, status = 'trial', start_date = %s, 
                       end_date = %s, auto_renew = FALSE, updated_at = %s 
                   WHERE company_id = %s""",
                (pro_plan['id'], start_date, end_date, datetime.utcnow(), company_id)
            )
        else:
            create_company_subscription(
                company_id=company_id,
                plan_id=pro_plan['id'],
                start_date=start_date,
                end_date=end_date,
                status='trial',
                auto_renew=False
            )
        
        # Update company
        mutate(
            """UPDATE companies 
               SET plan_id = %s, subscription_status = 'trial', 
                   subscription_start = %s, subscription_end = %s 
               WHERE id = %s""",
            (pro_plan['id'], start_date, end_date, company_id)
        )
        
        flash('14-day trial started! You now have access to all Professional features.', 'success')
        return redirect(url_for('subscription.manage_subscription'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error starting trial.', 'danger')
        return redirect(url_for('dashboard.index'))