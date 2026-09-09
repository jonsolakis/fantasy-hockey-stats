"""Provider boundary for external hockey-stat sources.

Only adapters in this module's implementations understand a vendor response.
The rest of the application works with the normalized records declared here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PlayerSeasonStatRecord:
    source_player_id: int
    first_name: str
    last_name: str
    position: str
    team_abbreviation: str
    games_played: int = 0
    goals: int = 0
    assists: int = 0
    shots: int = 0
    hits: int = 0
    blocked_shots: int = 0
    penalty_minutes: int = 0
    plus_minus: int = 0
    power_play_goals: int = 0
    power_play_assists: int = 0
    shorthanded_goals: int = 0
    shorthanded_assists: int = 0


@dataclass(frozen=True)
class SkaterSeasonStats:
    season_id: int
    game_type: int
    skater_stats: tuple[PlayerSeasonStatRecord, ...]
    raw_payload: dict


@dataclass(frozen=True)
class GoalieSeasonStatRecord:
    source_player_id: int
    first_name: str
    last_name: str
    team_abbreviation: str
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    ot_losses: int = 0
    saves: int = 0
    shots_against: int = 0
    goals_against: int = 0
    shutouts: int = 0
    save_percentage: float = 0.0


@dataclass(frozen=True)
class GoalieSeasonStats:
    season_id: int
    game_type: int
    goalie_stats: tuple[GoalieSeasonStatRecord, ...]
    raw_payload: dict


class StatsProvider(Protocol):
    """External source contract; swap providers without changing the domain layer."""

    name: str

    def fetch_skater_season_stats(self, season_id: int, game_type: int = 2) -> SkaterSeasonStats:
        """Return aggregate skater stats for one season and game type."""

    def fetch_goalie_season_stats(self, season_id: int, game_type: int = 2) -> GoalieSeasonStats:
        """Return aggregate goalie stats for one season and game type."""
