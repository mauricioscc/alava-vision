"""Database configuration and session management."""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Database:
    """Manages SQLAlchemy engine and sessions."""

    _instance: "Database | None" = None
    _engine = None
    _session_factory = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._engine is not None:
            return
        db_path = os.getenv("DATABASE_PATH", "data/database.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Enable WAL mode for better concurrent access
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self._session_factory = sessionmaker(bind=self._engine)

    @property
    def engine(self):
        return self._engine

    def create_all(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self._engine)

    def get_session(self) -> Session:
        """Create a new session."""
        return self._session_factory()

    def drop_all(self) -> None:
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self._engine)