"""
SEMDS Database - Storage Layer

PostgreSQL/SQLite database connection management.

Provides:
- init_database: Initialize database
- get_session: Get database session
- get_engine: Get database engine
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from storage.models import Base

# Global engine and session factory
_engine = None
_SessionFactory = None


def get_database_url() -> str:
    """
    Get database connection URL.

    Priority:
    1. DATABASE_URL environment variable (PostgreSQL)
    2. SEMDS_DB_PATH environment variable (SQLite)
    3. Default SQLite path

    Returns:
        Database connection URL
    """
    # Check for PostgreSQL URL first
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Handle asyncpg URL format if needed
        if database_url.startswith("postgresql://"):
            return database_url
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)

    # Fallback to SQLite
    db_path = os.environ.get("SEMDS_DB_PATH")
    if db_path:
        return f"sqlite:///{os.path.abspath(db_path)}"

    # Default SQLite path
    default_path = Path(__file__).parent / "semds.db"
    return f"sqlite:///{default_path.absolute()}"


def get_engine(db_path: str | None = None) -> Engine:
    """
    Get or create database engine.

    Args:
        db_path: Optional database path. If provided, creates a new engine for
                that path. If None, returns the global engine.

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if db_path is not None:
        # Create a new engine for the specified path (used in tests)
        database_url = f"sqlite:///{db_path}"
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=os.environ.get("SEMDS_LOG_LEVEL") == "DEBUG",
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma_connect(dbapi_conn: Any, connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    if _engine is None:
        database_url = get_database_url()

        # Configure engine arguments based on database type
        if database_url.startswith("postgresql"):
            # PostgreSQL configuration
            _engine = create_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=os.environ.get("SEMDS_LOG_LEVEL") == "DEBUG",
            )
        else:
            # SQLite configuration
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=os.environ.get("SEMDS_LOG_LEVEL") == "DEBUG",
            )

            # SQLite foreign key support
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_factory(db_path: str | None = None) -> sessionmaker[Session]:
    """
    Get or create session factory.

    Args:
        db_path: Optional database path. If provided, creates a new factory for
                that path.

    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionFactory

    if db_path is not None:
        # Create a new factory for the specified path (used in tests)
        engine = get_engine(db_path)
        return sessionmaker(bind=engine)

    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine)

    return _SessionFactory


def get_session(db_path: str | None = None) -> Session:
    """
    Get database session.

    Args:
        db_path: Optional database path. If provided, creates a new session for
                that path.

    Returns:
        SQLAlchemy Session instance
    """
    factory = get_session_factory(db_path)
    return factory()


def init_database(db_path: str | None = None) -> Engine:
    """
    Initialize database tables.

    Args:
        db_path: Optional database path. If provided, initializes that database.

    Returns:
        SQLAlchemy Engine instance

    Creates all tables defined in models.
    Safe to call multiple times (will not recreate existing tables).
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine


def drop_database(db_path: str | None = None) -> None:
    """
    Drop all database tables.

    Args:
        db_path: Optional database path. If provided, drops tables from that database.

    WARNING: This will delete all data!
    """
    engine = get_engine(db_path)
    Base.metadata.drop_all(bind=engine)


def reset_database(db_path: str | None = None) -> None:
    """
    Reset database (drop and recreate).

    Args:
        db_path: Optional database path. If provided, resets that database.

    WARNING: This will delete all data!
    """
    drop_database(db_path)
    init_database(db_path)


def is_postgresql() -> bool:
    """
    Check if using PostgreSQL.

    Returns:
        True if using PostgreSQL, False if SQLite
    """
    return get_database_url().startswith("postgresql")


def close_database() -> None:
    """
    Close database connection and cleanup resources.

    Call this when shutting down the application.
    """
    global _engine, _SessionFactory

    if _SessionFactory is not None:
        _SessionFactory = None

    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_db_path() -> str:
    """
    Get database file path for SQLite.

    Returns:
        Path to SQLite database file as string
    """
    url = get_database_url()
    if url.startswith("sqlite:///"):
        return str(Path(url.replace("sqlite:///", "")))
    raise ValueError("Not using SQLite database")


def get_db_session(db_path: str | None = None) -> Generator[Session, None, None]:
    """
    Get database session as a generator.

    Args:
        db_path: Optional database path. If provided, creates a new session for
                that path.

    Usage:
        gen = get_db_session()
        session = next(gen)
        # use session
        try:
            next(gen)  # closes session
        except StopIteration:
            pass

    Yields:
        SQLAlchemy Session
    """
    factory = get_session_factory(db_path)
    session = factory()
    try:
        yield session
    finally:
        session.close()


# Legacy compatibility alias
SessionLocal = get_session_factory
