"""
Database connection helper (MySQL - Railway)
"""
import logging
import os
import time
import mysql.connector
from mysql.connector import pooling, Error
from flask import current_app, g

logger = logging.getLogger(__name__)

# Global connection pool
pool = None


def _parse_database_url(database_url):
    """Parse MySQL connection URL to dict."""
    # Format: mysql://user:password@host:port/database
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', '')
    
    # Split credentials from host
    if '@' in database_url:
        credentials, host_db = database_url.split('@')
        user, password = credentials.split(':')
    else:
        return None
    
    # Split host and database
    if '/' in host_db:
        host_port, database = host_db.split('/')
    else:
        host_port = host_db
        database = 'railway'
    
    # Split host and port
    if ':' in host_port:
        host, port = host_port.split(':')
        port = int(port)
    else:
        host = host_port
        port = 3306
    
    return {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port,
        'autocommit': False,
        'raise_on_warnings': False,
        'connection_timeout': 10,
    }


def _get_connection_args(cfg):
    """Get connection arguments for MySQL database."""
    # Prefer DATABASE_URL from environment (standard for cloud platforms)
    if cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL'):
        database_url = cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL')
        return _parse_database_url(database_url)
    
    # Fallback to individual environment variables
    return {
        'host': cfg.get('DB_HOST') or os.getenv('DB_HOST'),
        'user': cfg.get('DB_USER') or os.getenv('DB_USER'),
        'password': cfg.get('DB_PASSWORD') or os.getenv('DB_PASSWORD'),
        'database': cfg.get('DB_NAME', 'railway') or os.getenv('DB_NAME', 'railway'),
        'port': int(cfg.get('DB_PORT', 3306) or os.getenv('DB_PORT', 3306)),
        'autocommit': False,
        'raise_on_warnings': False,
        'connection_timeout': 10,
    }


def init_pool(app):
    """Initialize connection pool (call once at app startup)."""
    global pool

    cfg = app.config
   

    # Connect to MySQL database
    try:
        conn_args = _get_connection_args(cfg)
        pool = pooling.MySQLConnectionPool(
            pool_name='hr_system_pool',
            pool_size=5,
            pool_reset_session=True,
            **conn_args
        )
        logger.info("✅ Connected to MySQL database (Railway)")
    except Error as e:
        logger.error("❌ Failed to connect to MySQL database: %s", e)
        pool = None


def get_db():
    """Return (or create) a per-request MySQL connection."""
    if 'db' not in g:
        cfg = current_app.config
        max_retries = 2
        retry_delay = 1  # seconds

        try:
            if pool:
                g.db = pool.get_connection()
            else:
                # Direct connection to MySQL with retries
                conn_args = _get_connection_args(cfg)
                
                for attempt in range(max_retries + 1):
                    try:
                        logger.debug(f"Connection attempt {attempt + 1}/{max_retries + 1}: {conn_args.get('host', 'unknown')}")
                        g.db = mysql.connector.connect(**conn_args)
                        logger.info("✅ Connected to MySQL database")
                        break
                    except Error as e:
                        if attempt < max_retries:
                            logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)[:80]}")
                            time.sleep(retry_delay)
                        else:
                            logger.error(f"DB connection error (final attempt): {e}")
                            raise RuntimeError(
                                "Database connection failed after retries. "
                                "Ensure DATABASE_URL or DB_* environment variables are set correctly. "
                                f"Error: {str(e)[:100]}"
                            )
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"DB connection error: {e}")
            raise

    return g.db


def _close_db(exc=None):
    """Close database connection."""
    db = g.pop('db', None)

    if db is not None:
        try:
            db.close()
        except Exception as e:
            logger.error("Error closing DB connection: %s", e)


def init_db(app):
    """Initialize DB helpers (call in app factory)."""
    init_pool(app)
    app.teardown_appcontext(_close_db)


def query(sql: str, params: tuple = (), one: bool = False):
    """
    Execute a SELECT query and return results as dictionaries.
    """
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(sql, params)
        result = cur.fetchone() if one else cur.fetchall()
        return result

    except Error as exc:
        logger.error("DB query error: %s | SQL: %s", exc, sql)
        raise

    finally:
        cur.close()


def mutate(sql: str, params: tuple = ()):
    """
    Execute INSERT / UPDATE / DELETE
    Returns last inserted ID for INSERT statements, True for UPDATE/DELETE
    """
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(sql, params)
        
        # For INSERT statements, return the last inserted ID
        if sql.strip().upper().startswith('INSERT'):
            last_id = cur.lastrowid
            db.commit()
            return last_id
        else:
            db.commit()
            return True

    except Error as exc:
        db.rollback()
        logger.error("DB mutate error: %s | SQL: %s", exc, sql)
        raise

    finally:
        cur.close()


def begin_transaction():
    """Start a database transaction for batch operations."""
    conn = get_db()
    if conn:
        conn.autocommit = False
        conn.start_transaction()
    return conn


def commit_transaction(conn):
    """Commit the current transaction."""
    try:
        if conn:
            conn.commit()
            logger.info("Transaction committed successfully")
    except Error as e:
        if conn:
            conn.rollback()
        logger.error("Transaction commit failed: %s", e)
        raise


def rollback_transaction(conn):
    """Rollback the current transaction."""
    try:
        if conn:
            conn.rollback()
            logger.warning("Transaction rolled back")
    except Error as e:
        logger.error("Transaction rollback failed: %s", e)
        raise