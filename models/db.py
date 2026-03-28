"""
Database connection helper.
  - get_db()        → returns a live connection stored in Flask's 'g'
  - query()         → executes SQL and returns results
  - mutate()        → executes INSERT / UPDATE / DELETE and commits
  - init_db(app)    → registers teardown hook
"""
import logging
import mysql.connector
from flask import current_app, g

logger = logging.getLogger(__name__)


def get_db():
    """Return (or create) a per-request MySQL connection."""
    if 'db' not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg['MYSQL_HOST'],
            user=cfg['MYSQL_USER'],
            password=cfg['MYSQL_PASSWORD'],
            database=cfg['MYSQL_DB'],
            port=cfg['MYSQL_PORT'],
            autocommit=False,
            charset='utf8mb4',
        )
    return g.db


def _close_db(exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(_close_db)


def query(sql: str, params: tuple = (), one: bool = False):
    """
    Execute a SELECT query.
      one=True  → return a single dict (or None)
      one=False → return a list of dicts
    """
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
    except mysql.connector.Error as exc:
        logger.error("DB query error: %s | SQL: %s", exc, sql)
        raise
    finally:
        cur.close()


def mutate(sql: str, params: tuple = ()):
    """
    Execute an INSERT / UPDATE / DELETE, commit, and return lastrowid.
    """
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        db.commit()
        return cur.lastrowid
    except mysql.connector.Error as exc:
        db.rollback()
        logger.error("DB mutate error: %s | SQL: %s", exc, sql)
        raise
    finally:
        cur.close()