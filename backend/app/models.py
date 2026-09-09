from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ScoringProfile(Base):
    __tablename__ = "scoring_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    rules: Mapped[list[ScoringRule]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class ScoringRule(Base):
    __tablename__ = "scoring_rules"
    __table_args__ = (UniqueConstraint("profile_id", "stat_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scoring_profiles.id"))
    stat_key: Mapped[str] = mapped_column(String(64))
    points: Mapped[float] = mapped_column(Float)
    profile: Mapped[ScoringProfile] = relationship(back_populates="rules")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    abbreviation: Mapped[str] = mapped_column(String(3), unique=True)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_player_id: Mapped[int] = mapped_column(unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(8))


class SkaterSeasonStat(Base):
    __tablename__ = "skater_season_stats"
    __table_args__ = (UniqueConstraint("player_id", "season_id", "game_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    season_id: Mapped[int] = mapped_column(Integer, index=True)
    game_type: Mapped[int] = mapped_column(Integer, default=2)
    team_abbreviations: Mapped[str] = mapped_column(String(32))
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    hits: Mapped[int] = mapped_column(Integer, default=0)
    blocked_shots: Mapped[int] = mapped_column(Integer, default=0)
    penalty_minutes: Mapped[int] = mapped_column(Integer, default=0)
    plus_minus: Mapped[int] = mapped_column(Integer, default=0)
    power_play_goals: Mapped[int] = mapped_column(Integer, default=0)
    power_play_assists: Mapped[int] = mapped_column(Integer, default=0)
    shorthanded_goals: Mapped[int] = mapped_column(Integer, default=0)
    shorthanded_assists: Mapped[int] = mapped_column(Integer, default=0)


class GoalieSeasonStat(Base):
    __tablename__ = "goalie_season_stats"
    __table_args__ = (UniqueConstraint("player_id", "season_id", "game_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    season_id: Mapped[int] = mapped_column(Integer, index=True)
    game_type: Mapped[int] = mapped_column(Integer, default=2)
    team_abbreviation: Mapped[str] = mapped_column(String(3))
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ot_losses: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    shots_against: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    shutouts: Mapped[int] = mapped_column(Integer, default=0)
    save_percentage: Mapped[float] = mapped_column(Float, default=0)


class RawSourcePayload(Base):
    __tablename__ = "raw_source_payloads"
    __table_args__ = (UniqueConstraint("provider_name", "resource_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(64))
    resource_key: Mapped[str] = mapped_column(String(128))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    payload: Mapped[str] = mapped_column()
