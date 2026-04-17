"""
Database connection helper (PostgreSQL - Supabase)
"""
import logging
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from flask import current_app, g

logger = logging.getLogger(__name__)

# Global connection pool
pool = None


def _get_connection_args(cfg):
    """Get connection arguments for Supabase/online database only."""
    # Prefer DATABASE_URL from environment (standard for cloud platforms)
    if cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL'):
        database_url = cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL')
        
        # Remove pgbouncer parameter if present (psycopg2 doesn't recognize it)
        database_url = database_url.replace('?pgbouncer=true', '').replace('&pgbouncer=true', '')
        
        # Add TCP keepalive and connection parameters for psycopg2
        if '?' not in database_url:
            database_url += '?sslmode=require&connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5'
        else:
            # Already has parameters, just add our keepalive settings
            database_url += '&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5'
        
        return {'dsn': database_url}
    
    # Fallback to individual environment variables
    return {
        'host': cfg.get('DB_HOST') or os.getenv('DB_HOST'),
        'user': cfg.get('DB_USER') or os.getenv('DB_USER'),
        'password': cfg.get('DB_PASSWORD') or os.getenv('DB_PASSWORD'),
        'dbname': cfg.get('DB_NAME', 'postgres') or os.getenv('DB_NAME', 'postgres'),
        'port': int(cfg.get('DB_PORT', 5432) or os.getenv('DB_PORT', 5432)),
        'sslmode': 'require',
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    }


def init_pool(app):
    """Initialize connection pool (call once at app startup)."""
    global pool

    cfg = app.config
    print("DB_HOST =", cfg.get('DB_HOST'))

    # Connect to Supabase/online database only
    try:
        pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **_get_connection_args(cfg)
        )
        logger.info("✅ Connected to Supabase database")
    except Exception as e:
        logger.error("❌ Failed to connect to Supabase: %s", e)
        pool = None


def get_db():
    """Return (or create) a per-request PostgreSQL connection to Supabase."""
    if 'db' not in g:
        cfg = current_app.config
        max_retries = 2
        retry_delay = 1  # seconds

        try:
            if pool:
                g.db = pool.getconn()
            else:
                # Direct connection to Supabase/online database with retries
                conn_args = _get_connection_args(cfg)
                
                for attempt in range(max_retries + 1):
                    try:
                        logger.debug(f"Connection attempt {attempt + 1}/{max_retries + 1}: {conn_args.get('dsn', conn_args.get('host', 'unknown'))}")
                        g.db = psycopg2.connect(**conn_args)
                        logger.info("✅ Connected to Supabase database")
                        break
                    except (psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
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
    """Return connection to pool or close it."""
    db = g.pop('db', None)

    if db is not None:
        try:
            if pool:
                pool.putconn(db)
            else:
                db.close()
        except Exception as e:
            logger.error("Error closing DB connection: %s", e)


def init_db(app):
    """Initialize DB helpers (call in app factory)."""
    init_pool(app)
    app.teardown_appcontext(_close_db)


def query(sql: str, params: tuple = (), one: bool = False):
    """
    Execute a SELECT query.
    """
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(sql, params)
        result = cur.fetchone() if one else cur.fetchall()
        return result

    except Exception as exc:
        logger.error("DB query error: %s | SQL: %s", exc, sql)
        raise

    finally:
        cur.close()


def mutate(sql: str, params: tuple = ()):
    """
    Execute INSERT / UPDATE / DELETE
    """
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(sql, params)
        db.commit()
        return True

    except Exception as exc:
        db.rollback()
        logger.error("DB mutate error: %s | SQL: %s", exc, sql)
        raise

    finally:
        cur.close()