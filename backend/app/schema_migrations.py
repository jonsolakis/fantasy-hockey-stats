"""Helpers for applying the versioned database schema."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_schema() -> None:
    """Upgrade the configured database to the latest Alembic revision."""
    migration_directory = Path(__file__).resolve().parent / "alembic"
    config = Config()
    config.set_main_option("script_location", str(migration_directory))
    command.upgrade(config, "head")
