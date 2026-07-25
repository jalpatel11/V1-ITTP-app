"""Database Connection and Session Management Module.

Sets up SQLAlchemy engine, session maker, base ORM class, and database initialization.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.utils.logger import log_error, log_info

# Configure connect_args for SQLite threading compatibility if using SQLite
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator that provides a database session for API requests.

    Yields:
        Session: Active SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log_error("get_db", "Database transaction failed", error=e)
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initializes database tables according to defined ORM models."""
    try:
        # Import models so Base.metadata is fully populated before create_all
        import app.models.domain  # noqa: F401
        Base.metadata.create_all(bind=engine)
        log_info("init_db", "Database schema tables initialized successfully.")
    except Exception as e:
        log_error("init_db", "Failed to initialize database tables", error=e)
        raise
