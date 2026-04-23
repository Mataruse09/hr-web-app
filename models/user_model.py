from models.db import query, mutate
from datetime import datetime


def get_by_username(username: str, company_id: int):
    normalized_username = username.strip().lower()
    return query(
        "SELECT * FROM users WHERE username = %s AND company_id = %s AND is_active = TRUE",
        (normalized_username, company_id), one=True
    )


def get_by_username_email(username: str, email: str, company_id: int):
    return query(
        "SELECT * FROM users WHERE (username = %s OR email = %s) AND company_id = %s",
        (username.strip().lower(), email.strip().lower(), company_id),
        one=True
    )


def get_by_id(user_id: int, company_id: int):
    return query(
        "SELECT id, company_id, username, email, full_name, role "
        "FROM users WHERE id = %s AND company_id = %s",
        (user_id, company_id), one=True
    )


def create_user(company_id: int, username: str, email: str, full_name: str, password_hash: str, role: str = 'HR'):
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()

    # Check if username exists ONLY in this company
    existing_user = query(
        "SELECT id FROM users WHERE username = %s AND company_id = %s",
        (normalized_username, company_id), one=True
    )
    if existing_user:
        raise ValueError(f"Username '{normalized_username}' already exists in this company.")

    # Check if email exists in this company
    # ✅ NOTE: Schema has UNIQUE(company_id, email) - allows same email across different companies
    existing_email_same_company = query(
        "SELECT id FROM users WHERE company_id = %s AND email = %s",
        (company_id, normalized_email), one=True
    )
    if existing_email_same_company:
        raise ValueError(f"Email '{normalized_email}' already exists in this company.")

    role_map = {
        'hr': 'HR',
        'chro': 'CHRO',
        'admin': 'Admin',
        'manager': 'Manager',
        'employee': 'Employee',
        'company_admin': 'company_admin'
    }
    normalized_role = role_map.get(role.strip().lower(), role.strip().title())

    return mutate(
        "INSERT INTO users (company_id, username, password_hash, email, full_name, role) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (company_id, normalized_username, password_hash, normalized_email, full_name.strip(), normalized_role)
    )


def update_last_login(user_id: int):
    mutate(
        "UPDATE users SET last_login = %s WHERE id = %s",
        (datetime.utcnow(), user_id)
    )


def update_password(user_id: int, new_password_hash: str):
    return mutate(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (new_password_hash, user_id)
    )


def get_all_users(company_id: int):
    return query(
        "SELECT id, username, email, full_name, role, is_active, last_login "
        "FROM users WHERE company_id = %s ORDER BY full_name",
        (company_id,)
    )


def get_user_by_id(user_id: int, company_id: int):
    return query(
        "SELECT id, company_id, username, email, full_name, role, is_active "
        "FROM users WHERE id=%s AND company_id=%s",
        (user_id, company_id), one=True
    )


def update_user_role(user_id: int, company_id: int, role: str):
    return mutate(
        "UPDATE users SET role=%s WHERE id=%s AND company_id=%s",
        (role, user_id, company_id)
    )


def update_user_info(user_id: int, company_id: int, email: str, full_name: str):
    return mutate(
        "UPDATE users SET email=%s, full_name=%s WHERE id=%s AND company_id=%s",
        (email.strip().lower(), full_name.strip(), user_id, company_id)
    )


def get_by_username_any(username: str):
    normalized_username = username.strip().lower()
    return query(
        "SELECT * FROM users WHERE username = %s AND is_active = TRUE AND role = 'Employee'",
        (normalized_username,), one=True
    )


# =========================
# RESET TOKEN
# =========================

def save_reset_token(user_id: int, token: str, expiry: datetime):
    return mutate(
        "UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE id=%s",
        (token, expiry, user_id)
    )


def get_by_reset_token(token: str, company_id: int):
    if not token:
        return None

    return query(
        "SELECT * FROM users WHERE reset_token=%s AND company_id=%s "
        "AND is_active=TRUE AND reset_token_expiry > %s",
        (token, company_id, datetime.utcnow()), one=True
    )


def clear_reset_token(user_id: int):
    return mutate(
        "UPDATE users SET reset_token=NULL, reset_token_expiry=NULL WHERE id=%s",
        (user_id,)
    )


# =========================
# ROLE MANAGEMENT
# =========================

def assign_role_to_user(user_id: int, company_id: int, role: str):
    """Assign a role to a user in the user_roles table"""
    return mutate(
        "INSERT INTO user_roles (user_id, company_id, role) "
        "VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE role = %s",
        (user_id, company_id, role, role)
    )


def get_user_roles(user_id: int, company_id: int):
    """Get all roles for a user in a company"""
    return query(
        "SELECT role FROM user_roles WHERE user_id = %s AND company_id = %s",
        (user_id, company_id)
    )


def remove_role_from_user(user_id: int, company_id: int, role: str = None):
    """Remove role(s) from a user"""
    if role:
        return mutate(
            "DELETE FROM user_roles WHERE user_id = %s AND company_id = %s AND role = %s",
            (user_id, company_id, role)
        )
    else:
        return mutate(
            "DELETE FROM user_roles WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )