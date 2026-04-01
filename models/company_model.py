from models.db import query, mutate


def create_company(name, industry, address, phone, email, website):
    return mutate(
        "INSERT INTO companies (name, industry, address, phone, email, website) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (name, industry, address, phone, email, website)
    )


def get_by_id(company_id: int):
    return query(
        "SELECT id, name, industry, address, phone, email, website, is_active "
        "FROM companies WHERE id = %s AND is_active = 1",
        (company_id,), one=True
    )


def get_by_name(name: str):
    return query(
        "SELECT id, name, industry, address, phone, email, website, is_active "
        "FROM companies WHERE name = %s AND is_active = 1",
        (name,), one=True
    )


def all_active_companies():
    return query(
        "SELECT id, name FROM companies WHERE is_active = 1 ORDER BY name"
    )
