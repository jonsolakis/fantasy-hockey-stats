from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def database_url() -> str:
    """Return an explicit URL or construct one from PostgreSQL environment variables."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    postgres_host = os.getenv("POSTGRES_HOST")
    if postgres_host:
        required = {key: os.getenv(key) for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")}
        missing = sorted(key for key, value in required.items() if not value)
        if missing:
            raise RuntimeError(f"PostgreSQL is configured but missing environment variables: {', '.join(missing)}")
        return URL.create(
            "postgresql+psycopg",
            username=required["POSTGRES_USER"],
            password=required["POSTGRES_PASSWORD"],
            host=postgres_host,
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=required["POSTGRES_DB"],
        ).render_as_string(hide_password=False)

    return "sqlite:///./data/fantasy-hockey.db"


DATABASE_URL = database_url()

if DATABASE_URL.startswith("sqlite:///"):
    database_path = DATABASE_URL.removeprefix("sqlite:///")
    if database_path != ":memory:":
        Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(Engine, "connect")
def configure_sqlite(dbapi_connection: object, connection_record: object) -> None:
    """Set connection-level SQLite safety and concurrency settings."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
