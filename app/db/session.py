import logging
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_db_url() -> str:
    """Resolves database URL preferring DATABASE_URL or SUPABASE_DB_URL, with local SQLite fallback if unreachable."""
    raw_url = settings.database_url or settings.supabase_db_url or os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if raw_url and not raw_url.startswith("sqlite"):
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)
        # Verify remote DB connectivity
        try:
            temp_engine = create_engine(raw_url, connect_args={"connect_timeout": 2})
            with temp_engine.connect() as conn:
                logger.info("Successfully connected to external PostgreSQL database.")
                return raw_url
        except Exception as e:
            logger.warning(f"External database unreachable ({e}). Gracefully falling back to local SQLite.")

    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../triage_data.sqlite"))
    return f"sqlite:///{sqlite_path}"


DB_URL = get_db_url()
is_sqlite = DB_URL.startswith("sqlite")

connect_args = {"check_same_thread": False, "timeout": 30.0} if is_sqlite else {"connect_timeout": 5}
pool_kwargs = {} if is_sqlite else {"pool_size": 5, "max_overflow": 10, "pool_recycle": 3600}

engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    **pool_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes database schema and configures WAL concurrency for SQLite."""
    try:
        from app.db import models  # noqa
        Base.metadata.create_all(bind=engine)
        if is_sqlite:
            with engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                conn.exec_driver_sql("PRAGMA busy_timeout=30000;")
        logger.info(f"Database schema initialized successfully using engine: {engine.url.drivername}")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a clean database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
