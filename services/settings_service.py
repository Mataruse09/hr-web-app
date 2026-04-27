"""
System Settings Service - Manage company-level configurations
"""
from models.db import query, mutate
import json
import logging
import time

logger = logging.getLogger(__name__)

# Simple in-memory cache for settings (cache for 5 minutes)
_settings_cache = {}
_cache_ttl = 300  # 5 minutes

DEFAULT_SETTINGS = {
    'theme_primary_color': '#1a2b4a',
    'theme_secondary_color': '#3498db',
    'theme_background_color': '#ecf0f1',
    'theme_accent_color': '#e74c3c',
    'company_logo_url': '',
    'company_branding': 'MatinexHR',
    'notification_email_enabled': True,
    'employee_self_service_enabled': True,
    'attendance_geolocation_required': False,
    'payroll_currency': 'USD',
    'work_hours_per_day': '8',
    'weekend_days': 'Saturday,Sunday',
    'leave_approval_required': True,
    'overtime_enabled': True,
    'tax_calculation_method': 'progressive',
    'financial_year_start': '01-01',
}


def _get_cache_key(company_id):
    return f"settings_{company_id}"


def _get_cached_settings(company_id):
    """Get cached settings if available and not expired."""
    cache_key = _get_cache_key(company_id)
    if cache_key in _settings_cache:
        cached_data, timestamp = _settings_cache[cache_key]
        if time.time() - timestamp < _cache_ttl:
            return cached_data
    return None


def _set_cached_settings(company_id, settings):
    """Cache settings with timestamp."""
    cache_key = _get_cache_key(company_id)
    _settings_cache[cache_key] = (settings, time.time())


def clear_settings_cache(company_id=None):
    """Clear settings cache for a company or all."""
    if company_id:
        cache_key = _get_cache_key(company_id)
        _settings_cache.pop(cache_key, None)
    else:
        _settings_cache.clear()


def get_setting(company_id: int, setting_key: str, default=None):
    """Get a single setting value."""
    # Try cache first
    cached = _get_cached_settings(company_id)
    if cached is not None and setting_key in cached:
        return cached.get(setting_key, default)
    
    try:
        result = query("""
            SELECT setting_value, setting_type FROM system_settings
            WHERE company_id = %s AND setting_key = %s
        """, (company_id, setting_key), one=True)
        
        if result:
            value = result['setting_value']
            setting_type = result['setting_type']
            
            # Parse value based on type
            if setting_type == 'boolean':
                return value.lower() in ['true', '1', 'yes']
            elif setting_type == 'integer':
                return int(value)
            elif setting_type == 'json':
                return json.loads(value)
            else:
                return value
        
        return default
    except Exception as e:
        logger.error(f"Failed to get setting {setting_key}: {e}")
        return default


def get_all_settings(company_id: int) -> dict:
    """Get all settings for a company (with caching)."""
    # Check cache first
    cached = _get_cached_settings(company_id)
    if cached is not None:
        return cached
    
    try:
        results = query("""
            SELECT setting_key, setting_value, setting_type FROM system_settings
            WHERE company_id = %s
        """, (company_id,))
        
        settings = {}
        for row in results:
            key = row['setting_key']
            value = row['setting_value']
            stype = row['setting_type']
            
            if stype == 'boolean':
                settings[key] = value.lower() in ['true', '1', 'yes']
            elif stype == 'integer':
                settings[key] = int(value)
            elif stype == 'json':
                settings[key] = json.loads(value)
            else:
                settings[key] = value
        
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return {}


def set_setting(company_id: int, setting_key: str, setting_value, setting_type: str = 'string'):
    """Update or create a setting."""
    try:
        # Convert value to string for storage
        if setting_type == 'json':
            value_str = json.dumps(setting_value)
        else:
            value_str = str(setting_value)
        
        mutate("""
            INSERT INTO system_settings (company_id, setting_key, setting_value, setting_type, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                setting_value = VALUES(setting_value),
                setting_type = VALUES(setting_type),
                updated_at = NOW()
        """, (company_id, setting_key, value_str, setting_type))
        
        # Clear cache after updating
        clear_settings_cache(company_id)
        
        logger.info(f"Setting {setting_key} updated for company {company_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to set setting {setting_key}: {e}")
        return False


def initialize_default_settings(company_id: int):
    """Initialize default settings for a new company."""
    try:
        for key, value in DEFAULT_SETTINGS.items():
            if isinstance(value, bool):
                stype = 'boolean'
                val = 'true' if value else 'false'
            elif isinstance(value, int):
                stype = 'integer'
                val = str(value)
            else:
                stype = 'string'
                val = str(value)
            
            set_setting(company_id, key, val, stype)
        
        logger.info(f"Default settings initialized for company {company_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize settings: {e}")
        return False


def update_theme(company_id: int, theme_data: dict) -> bool:
    """Update company theme settings."""
    try:
        for key, value in theme_data.items():
            if key.startswith('theme_'):
                set_setting(company_id, key, value, 'string')
        return True
    except Exception as e:
        logger.error(f"Failed to update theme: {e}")
        return False


def get_theme(company_id: int) -> dict:
    """Get all theme settings for a company."""
    try:
        settings = get_all_settings(company_id)
        theme = {}
        for key, value in settings.items():
            if key.startswith('theme_'):
                theme[key] = value
        return theme
    except Exception as e:
        logger.error(f"Failed to get theme: {e}")
        return {}
