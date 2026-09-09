"""Helpers for applying the versioned database schema."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_schema() -> None:
    """Upgrade the configured database to the latest Alembic revision."""
    project_root = Path(__file__).resolve().parents[2]
    config = Config(project_root / "alembic.ini")
    config.set_main_option("script_location", str(project_root / "backend" / "alembic"))
    command.upgrade(config, "head")
