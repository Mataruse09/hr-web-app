"""
Database connection helper (PostgreSQL - Supabase)
"""
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from flask import current_app, g

logger = logging.getLogger(__name__)

# Global connection pool
pool = None


def _get_connection_args(cfg, use_local=False):
    """Get connection arguments. If use_local=True, try localhost PostgreSQL."""
    if use_local:
        return {
            'host': 'localhost',
            'user': os.getenv('LOCAL_DB_USER', 'postgres'),
            'password': os.getenv('LOCAL_DB_PASSWORD', 'postgres'),
            'dbname': os.getenv('LOCAL_DB_NAME', 'hr_system'),
            'port': int(os.getenv('LOCAL_DB_PORT', 5432)),
            'connect_timeout': 5,
        }
    
    # Prefer DATABASE_URL from environment (standard for cloud platforms)
    if cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL'):
        database_url = cfg.get('DATABASE_URL') or os.getenv('DATABASE_URL')
        # For Supabase, add connection parameters to the URL
        # Format: postgresql://user:password@host:port/dbname?sslmode=require&connect_timeout=10&statement_timeout=30000
        if '?' not in database_url:
            database_url += '?sslmode=require&connect_timeout=10&statement_timeout=30000'
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
        'statement_timeout': 30000,
    }


def init_pool(app):
    """Initialize connection pool (call once at app startup)."""
    global pool

    cfg = app.config
    print("DB_HOST =", cfg.get('DB_HOST'))

    # Try online database first
    try:
        pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **_get_connection_args(cfg)
        )
        logger.info("✅ Connected to online database")
    except Exception as e:
        logger.warning("⚠️  Online database failed: %s", e)
        logger.info("🔄 Trying local PostgreSQL fallback...")
        
        # Try local fallback
        try:
            pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **_get_connection_args(cfg, use_local=True)
            )
            logger.info("✅ Connected to local PostgreSQL fallback")
        except Exception as e2:
            logger.error("❌ Local fallback also failed: %s", e2)
            pool = None


def get_db():
    """Return (or create) a per-request PostgreSQL connection."""
    if 'db' not in g:
        cfg = current_app.config

        try:
            if pool:
                g.db = pool.getconn()
            else:
                # Try online first, then local fallback
                try:
                    conn_args = _get_connection_args(cfg)
                    logger.debug(f"Attempting connection to: {conn_args.get('dsn', conn_args.get('host', 'unknown'))}")
                    g.db = psycopg2.connect(**conn_args)
                    logger.info("✅ Connected to Supabase/Online database")
                except psycopg2.OperationalError as e:
                    logger.warning(f"⚠️  Online database failed (timeout/unreachable): {str(e)[:100]}")
                    logger.info("🔄 Attempting local PostgreSQL fallback...")
                    try:
                        g.db = psycopg2.connect(**_get_connection_args(cfg, use_local=True))
                        logger.info("✅ Connected to local PostgreSQL fallback")
                    except psycopg2.OperationalError as e2:
                        logger.error(f"❌ Both online and local database failed: {str(e2)[:100]}")
                        raise RuntimeError(
                            "Database connection failed. "
                            "Ensure DATABASE_URL or DB_* environment variables are set correctly. "
                            f"Error: {str(e)[:50]}"
                        )
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