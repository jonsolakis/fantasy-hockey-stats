"""Normalization and persistence for provider data."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import GoalieSeasonStat, Player, RawSourcePayload, SkaterSeasonStat
from .providers import (
    GoalieSeasonStatRecord,
    GoalieSeasonStats,
    PlayerSeasonStatRecord,
    SkaterSeasonStats,
    StatsProvider,
)


def import_skater_season_stats(
    session: Session, provider: StatsProvider, snapshot: SkaterSeasonStats
) -> int:
    """Atomically replace one season's skater-summary snapshot.

    A retry deletes and recreates the same season rows inside one transaction,
    so a completed command is idempotent and partial failures preserve the last
    successfully imported snapshot.
    """
    try:
        session.query(SkaterSeasonStat).filter(
            SkaterSeasonStat.season_id == snapshot.season_id,
            SkaterSeasonStat.game_type == snapshot.game_type,
        ).delete()

        for stat in snapshot.skater_stats:
            player = _upsert_player(session, stat)
            session.add(
                SkaterSeasonStat(
                    player_id=player.id,
                    season_id=snapshot.season_id,
                    game_type=snapshot.game_type,
                    team_abbreviations=stat.team_abbreviation,
                    games_played=stat.games_played,
                    goals=stat.goals,
                    assists=stat.assists,
                    shots=stat.shots,
                    hits=stat.hits,
                    blocked_shots=stat.blocked_shots,
                    penalty_minutes=stat.penalty_minutes,
                    plus_minus=stat.plus_minus,
                    power_play_goals=stat.power_play_goals,
                    power_play_assists=stat.power_play_assists,
                    shorthanded_goals=stat.shorthanded_goals,
                    shorthanded_assists=stat.shorthanded_assists,
                )
            )

        resource_key = f"skater/summary?seasonId={snapshot.season_id}&gameTypeId={snapshot.game_type}"
        raw_payload = session.scalar(
            select(RawSourcePayload).where(
                RawSourcePayload.provider_name == provider.name,
                RawSourcePayload.resource_key == resource_key,
            )
        )
        if raw_payload is None:
            raw_payload = RawSourcePayload(provider_name=provider.name, resource_key=resource_key)
            session.add(raw_payload)
        raw_payload.payload = json.dumps(snapshot.raw_payload, separators=(",", ":"))
        session.commit()
    except Exception:
        session.rollback()
        raise

    return len(snapshot.skater_stats)


def import_goalie_season_stats(
    session: Session, provider: StatsProvider, snapshot: GoalieSeasonStats
) -> int:
    """Atomically replace one season's goalie-summary snapshot."""
    try:
        session.query(GoalieSeasonStat).filter(
            GoalieSeasonStat.season_id == snapshot.season_id,
            GoalieSeasonStat.game_type == snapshot.game_type,
        ).delete()

        for stat in snapshot.goalie_stats:
            player = _upsert_player(session, stat, position="G")
            session.add(
                GoalieSeasonStat(
                    player_id=player.id,
                    season_id=snapshot.season_id,
                    game_type=snapshot.game_type,
                    team_abbreviation=stat.team_abbreviation,
                    games_played=stat.games_played,
                    wins=stat.wins,
                    losses=stat.losses,
                    ot_losses=stat.ot_losses,
                    saves=stat.saves,
                    shots_against=stat.shots_against,
                    goals_against=stat.goals_against,
                    shutouts=stat.shutouts,
                    save_percentage=stat.save_percentage,
                )
            )

        resource_key = f"goalie/summary?seasonId={snapshot.season_id}&gameTypeId={snapshot.game_type}"
        raw_payload = session.scalar(
            select(RawSourcePayload).where(
                RawSourcePayload.provider_name == provider.name,
                RawSourcePayload.resource_key == resource_key,
            )
        )
        if raw_payload is None:
            raw_payload = RawSourcePayload(provider_name=provider.name, resource_key=resource_key)
            session.add(raw_payload)
        raw_payload.payload = json.dumps(snapshot.raw_payload, separators=(",", ":"))
        session.commit()
    except Exception:
        session.rollback()
        raise

    return len(snapshot.goalie_stats)


def _upsert_player(
    session: Session, stat: PlayerSeasonStatRecord | GoalieSeasonStatRecord, *, position: str | None = None
) -> Player:
    player = session.scalar(select(Player).where(Player.source_player_id == stat.source_player_id))
    if player is None:
        player = Player(source_player_id=stat.source_player_id)
        session.add(player)
    player.first_name = stat.first_name
    player.last_name = stat.last_name
    player.position = position or stat.position
    session.flush()
    return player
