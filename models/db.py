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
            pool_size=15,  # Increased from 5 to handle more concurrent requests
            pool_reset_session=True,
            **conn_args
        )
        logger.info("✅ Connected to MySQL database (Railway)")
        
        # Run schema migrations if needed
        _run_migrations(pool)
        
    except Error as e:
        logger.error("❌ Failed to connect to MySQL database: %s", e)
        pool = None


def _run_migrations(pool):
    """Run database schema migrations to add missing columns."""
    try:
        conn = pool.get_connection()
        cur = conn.cursor()
        
        # Get existing columns in attendance table
        cur.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'attendance'
        """)
        existing_cols = {row[0] for row in cur.fetchall()}
        
        # Columns that should exist in attendance table based on schema
        required_cols = {
            'working_hours': "ALTER TABLE attendance ADD COLUMN working_hours DECIMAL(5,2) DEFAULT NULL AFTER status",
            'notes': "ALTER TABLE attendance ADD COLUMN notes VARCHAR(500) DEFAULT NULL AFTER working_hours",
            'recorded_by': "ALTER TABLE attendance ADD COLUMN recorded_by INT UNSIGNED DEFAULT NULL AFTER notes"
        }
        
        for col_name, alter_sql in required_cols.items():
            if col_name not in existing_cols:
                cur.execute(alter_sql)
                conn.commit()
                logger.info(f"✅ Migration: Added {col_name} column to attendance table")
        
        # Get existing columns in payroll_runs table
        cur.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'payroll_runs'
        """)
        payroll_cols = {row[0] for row in cur.fetchall()}
        
        # Columns that should exist in payroll_runs table
        payroll_required = {
            'overtime_hours': "ALTER TABLE payroll_runs ADD COLUMN overtime_hours DECIMAL(6,2) DEFAULT 0",
            'overtime_amount': "ALTER TABLE payroll_runs ADD COLUMN overtime_amount DECIMAL(15,2) DEFAULT 0",
            'prorated_salary': "ALTER TABLE payroll_runs ADD COLUMN prorated_salary DECIMAL(15,2) DEFAULT 0",
            'housing_allowance': "ALTER TABLE payroll_runs ADD COLUMN housing_allowance DECIMAL(15,2) DEFAULT 0",
            'transport_allowance': "ALTER TABLE payroll_runs ADD COLUMN transport_allowance DECIMAL(15,2) DEFAULT 0",
            'meal_allowance': "ALTER TABLE payroll_runs ADD COLUMN meal_allowance DECIMAL(15,2) DEFAULT 0",
            'performance_bonus': "ALTER TABLE payroll_runs ADD COLUMN performance_bonus DECIMAL(15,2) DEFAULT 0",
        }
        
        for col_name, alter_sql in payroll_required.items():
            if col_name not in payroll_cols:
                cur.execute(alter_sql)
                conn.commit()
                logger.info(f"✅ Migration: Added {col_name} column to payroll_runs table")
        
        cur.close()
        conn.close()
        
    except Error as e:
        logger.warning(f"Migration check failed (non-critical): {e}")


def get_db():
    """Return (or create) a per-request MySQL connection."""
    # Always try to get a fresh connection if the previous one was None or invalid
    # Remove any stale connection from g to allow retry
    if 'db' in g and (g.db is None or not hasattr(g.db, 'cursor') or not _is_connection_valid(g.db)):
        g.pop('db', None)
    
    if 'db' not in g:
        cfg = current_app.config
        max_retries = 1  # Reduced from 2 for faster fail
        retry_delay = 0.5  # Reduced from 1 for faster retry

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
                            # Set to None instead of raising, so calling code can handle gracefully
                            g.db = None
        except Exception as e:
            logger.error(f"DB connection error: {e}")
            g.db = None

    # Final safety check - ensure we return a valid connection or None
    if g.get('db') is None:
        return None
    
    # Verify the connection is actually usable
    if not _is_connection_valid(g.db):
        logger.warning("Existing DB connection is not valid, setting to None")
        g.db = None
        return None
    
    return g.db


def _is_connection_valid(db):
    """Check if a database connection is valid and connected."""
    try:
        if db is None:
            return False
        if not hasattr(db, 'is_connected'):
            return False
        return db.is_connected()
    except:
        return False


def _close_db(exc=None):
    """Close database connection and return it to the pool."""
    db = g.pop('db', None)

    if db is not None:
        try:
            if db.is_connected():
                db.close()  # Returns connection to the pool
            else:
                # Connection was already closed, create a new one for the pool
                pass
        except Exception as e:
            logger.debug("Error closing DB connection (non-critical): %s", e)


def init_db(app):
    """Initialize DB helpers (call in app factory)."""
    init_pool(app)
    app.teardown_appcontext(_close_db)


def query(sql: str, params: tuple = (), one: bool = False, max_retries: int = 3):
    """
    Execute a SELECT query and return results as dictionaries.
    Uses buffered cursor to prevent "Unread result found" errors.
    Includes retry logic for transient database errors.
    """
    import traceback
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Wrap get_db() in try-except to catch any issues
            try:
                db = get_db()
            except Exception as db_err:
                logger.error(f"Error getting database connection: {db_err}")
                # Try again instead of returning empty
                time.sleep(0.1)
                continue
            
            # Check if db connection is valid (more robust check)
            if not db or not hasattr(db, 'cursor'):
                # Try again - connection might be re-established
                logger.warning("Database connection is None or invalid - retrying")
                time.sleep(0.1)
                continue
            
            # Use buffered=True to fetch all results immediately and avoid unread result issues
            cur = db.cursor(dictionary=True, buffered=True)

            try:
                cur.execute(sql, params)
                result = cur.fetchone() if one else cur.fetchall()
                return result

            except Error as exc:
                logger.error("DB query error: %s | SQL: %s", exc, sql)
                raise

            finally:
                if cur:
                    cur.close()
                if db:
                    db.close()
                    
        except Error as e:
            last_error = e
            error_msg = str(e).lower()
            
            # Check if it's a transient error that warrants a retry
            transient_errors = [
                'lost connection',
                'connection timeout',
                'connection already closed',
                'server has gone away',
                'transaction already in progress',
                '2006',  # MySQL server has gone away
            ]
            
            is_transient = any(err in error_msg for err in transient_errors)
            
            if is_transient and attempt < max_retries - 1:
                logger.warning(f"Transient DB error (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(0.1 * (attempt + 1))  # Faster backoff
                continue
            else:
                logger.error("DB query error: %s | SQL: %s", e, sql)
                raise
    
    # If we get here, all retries failed
    logger.error(f"DB query failed after {max_retries} attempts: {last_error}")
    logger.error(traceback.format_exc())
    raise last_error


def mutate(sql: str, params: tuple = (), max_retries: int = 3):
    """
    Execute INSERT / UPDATE / DELETE
    Returns last inserted ID for INSERT statements, True for UPDATE/DELETE
    Includes retry logic for transient database errors.
    """
    import traceback
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Wrap get_db() in try-except to catch any issues
            try:
                db = get_db()
            except Exception as db_err:
                logger.error(f"Error getting database connection: {db_err}")
                # Try again instead of returning None
                time.sleep(0.1)
                continue
            
            # Check if db connection is valid (more robust check)
            if not db or not hasattr(db, 'cursor'):
                # Try again - connection might be re-established
                logger.warning("Database connection is None or invalid - retrying")
                time.sleep(0.1)
                continue
            
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
                if db:
                    db.rollback()
                logger.error("DB mutate error: %s | SQL: %s", exc, sql)
                raise

            finally:
                if cur:
                    cur.close()
                if db:
                    db.close()
                    
        except Error as e:
            last_error = e
            error_msg = str(e).lower()
            
            # Check if it's a transient error that warrants a retry
            transient_errors = [
                'lost connection',
                'connection timeout',
                'connection already closed',
                'server has gone away',
                'transaction already in progress',
                '2006',
            ]
            
            is_transient = any(err in error_msg for err in transient_errors)
            
            if is_transient and attempt < max_retries - 1:
                logger.warning(f"Transient DB error (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(0.1 * (attempt + 1))
                continue
            else:
                logger.error("DB mutate error: %s | SQL: %s", e, sql)
                raise
    
    logger.error(f"DB mutate failed after {max_retries} attempts: {last_error}")
    logger.error(traceback.format_exc())
    raise last_error


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