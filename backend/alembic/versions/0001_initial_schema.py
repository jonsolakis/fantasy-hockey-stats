"""Initial application schema.

This migration is intentionally safe to run against the prototype database
created with create_all(): it creates only tables that are still missing, then
records the database as being at this revision.
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "scoring_profiles" not in existing:
        op.create_table(
            "scoring_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False, unique=True),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    if "scoring_rules" not in existing:
        op.create_table(
            "scoring_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("profile_id", sa.Integer(), sa.ForeignKey("scoring_profiles.id"), nullable=False),
            sa.Column("stat_key", sa.String(length=64), nullable=False),
            sa.Column("points", sa.Float(), nullable=False),
            sa.UniqueConstraint("profile_id", "stat_key"),
        )
    if "teams" not in existing:
        op.create_table(
            "teams",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("abbreviation", sa.String(length=3), nullable=False, unique=True),
        )
    if "players" not in existing:
        op.create_table(
            "players",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source_player_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("first_name", sa.String(length=100), nullable=False),
            sa.Column("last_name", sa.String(length=100), nullable=False),
            sa.Column("position", sa.String(length=8), nullable=False),
        )
        op.create_index("ix_players_source_player_id", "players", ["source_player_id"])
    if "skater_season_stats" not in existing:
        op.create_table(
            "skater_season_stats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
            sa.Column("season_id", sa.Integer(), nullable=False),
            sa.Column("game_type", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("team_abbreviations", sa.String(length=32), nullable=False),
            sa.Column("games_played", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("shots", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("blocked_shots", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("plus_minus", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("power_play_goals", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("power_play_assists", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("shorthanded_goals", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("shorthanded_assists", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("player_id", "season_id", "game_type"),
        )
        op.create_index("ix_skater_season_stats_player_id", "skater_season_stats", ["player_id"])
        op.create_index("ix_skater_season_stats_season_id", "skater_season_stats", ["season_id"])
    if "goalie_season_stats" not in existing:
        op.create_table(
            "goalie_season_stats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
            sa.Column("season_id", sa.Integer(), nullable=False),
            sa.Column("game_type", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("team_abbreviation", sa.String(length=3), nullable=False),
            sa.Column("games_played", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ot_losses", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("shots_against", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("goals_against", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("shutouts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("save_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.UniqueConstraint("player_id", "season_id", "game_type"),
        )
        op.create_index("ix_goalie_season_stats_player_id", "goalie_season_stats", ["player_id"])
        op.create_index("ix_goalie_season_stats_season_id", "goalie_season_stats", ["season_id"])
    if "raw_source_payloads" not in existing:
        op.create_table(
            "raw_source_payloads",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provider_name", sa.String(length=64), nullable=False),
            sa.Column("resource_key", sa.String(length=128), nullable=False),
            sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("payload", sa.String(), nullable=False),
            sa.UniqueConstraint("provider_name", "resource_key"),
        )


def downgrade() -> None:
    raise NotImplementedError("The initial production schema is intentionally not downgraded.")
