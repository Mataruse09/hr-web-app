from models.db import query, mutate
from datetime import datetime


def get_by_username(username: str, company_id: int):
    return query(
        "SELECT * FROM users WHERE username = %s AND company_id = %s AND is_active = 1",
        (username, company_id), one=True
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
    return mutate(
        "INSERT INTO users (company_id, username, password_hash, email, full_name, role) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (company_id, username, password_hash, email, full_name, role)
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