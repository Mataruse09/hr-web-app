from models.db import query, mutate
from datetime import datetime


def get_by_username(username: str, company_id: int):
    normalized_username = username.strip().lower()
    return query(
        "SELECT * FROM users WHERE username = %s AND company_id = %s AND is_active = 1",
        (normalized_username, company_id), one=True
    )


def get_by_username_email(username: str, email: str, company_id: int):
    return query(
        "SELECT * FROM users WHERE (username = %s OR email = %s) AND company_id = %s",
        (username, email, company_id), one=True
    )


def get_by_id(user_id: int, company_id: int):
    return query(
        "SELECT id, company_id, username, email, full_name, role "
        "FROM users WHERE id = %s AND company_id = %s",
        (user_id, company_id), one=True
    )


def create_user(company_id: int, username: str, email: str, full_name: str, password_hash: str, role: str = 'HR'):
    normalized_username = username.strip().lower()
    normalized_role = role.strip().lower()
    if normalized_role == 'hr':
        normalized_role = 'HR'
    elif normalized_role == 'chro':
        normalized_role = 'CHRO'
    elif normalized_role == 'admin':
        normalized_role = 'Admin'
    elif normalized_role == 'manager':
        normalized_role = 'Manager'
    elif normalized_role == 'employee':
        normalized_role = 'Employee'
    else:
        normalized_role = role.strip().title()

    return mutate(
        "INSERT INTO users (company_id, username, password_hash, email, full_name, role) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (company_id, normalized_username, password_hash, email.strip().lower(), full_name.strip(), normalized_role)
    )


def update_last_login(user_id: int):
    mutate(
        "UPDATE users SET last_login = %s WHERE id = %s",
        (datetime.utcnow(), user_id)
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


def get_role_id(role_name: str):
    return query(
        "SELECT id FROM roles WHERE name = %s",
        (role_name,), one=True
    )


def assign_role_to_user(user_id: int, company_id: int, role_name: str):
    role = get_role_id(role_name)
    if not role:
        raise ValueError(f"Role '{role_name}' does not exist")

    return mutate(
        "INSERT IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (%s, %s, %s)",
        (user_id, role['id'], company_id)
    )


def seed_roles():
    default_roles = [
        ('company_admin', 'Manage company settings and users'),
        ('Admin', 'Full administrator'),
        ('HR', 'Human resources user'),
        ('Manager', 'Team manager'),
        ('Employee', 'Employee self-service'),
        ('CHRO', 'Chief HR Officer'),
    ]
    for role_name, description in default_roles:
        mutate(
            "INSERT IGNORE INTO roles (name, description) VALUES (%s, %s)",
            (role_name, description)
        )

