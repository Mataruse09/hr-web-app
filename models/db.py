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
    
    args = {
        'sslmode': 'require',
        'connect_timeout': 5,
    }

    if cfg.get('DATABASE_URL'):
        args['dsn'] = cfg['DATABASE_URL']
    else:
        args.update({
            'host': cfg['DB_HOST'],
            'user': cfg['DB_USER'],
            'password': cfg['DB_PASSWORD'],
            'dbname': cfg['DB_NAME'],
            'port': cfg['DB_PORT'],
        })

    return args


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
                    g.db = psycopg2.connect(**_get_connection_args(cfg))
                except Exception as e:
                    logger.debug("Online DB failed, trying local: %s", e)
                    g.db = psycopg2.connect(**_get_connection_args(cfg, use_local=True))
        except Exception as e:
            logger.error("DB connection error: %s", e)
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