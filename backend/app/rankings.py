"""Read models for scoring-profile based player rankings."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import GoalieSeasonStat, Player, ScoringProfile, SkaterSeasonStat

STAT_COLUMNS = {
    "goal": "goals",
    "assist": "assists",
    "shot": "shots",
    "hit": "hits",
    "blocked_shot": "blocked_shots",
    "penalty_minute": "penalty_minutes",
    "plus_minus": "plus_minus",
    "power_play_goal": "power_play_goals",
    "power_play_assist": "power_play_assists",
    "shorthanded_goal": "shorthanded_goals",
    "shorthanded_assist": "shorthanded_assists",
}

GOALIE_STAT_COLUMNS = {
    "win": "wins",
    "save": "saves",
    "goal_against": "goals_against",
    "shutout": "shutouts",
}


def player_rankings(
    session: Session, *, season_id: int, profile: ScoringProfile
) -> list[dict]:
    """Calculate rankings from immutable player-game stats and profile weights."""
    weights = {rule.stat_key: rule.points for rule in profile.rules}
    statement = (
        select(SkaterSeasonStat, Player)
        .join(Player, Player.id == SkaterSeasonStat.player_id)
        .where(SkaterSeasonStat.season_id == season_id, SkaterSeasonStat.game_type == 2)
    )
    players: dict[int, dict] = {}
    for stat, player in session.execute(statement):
        players[player.id] = {
            "player_id": player.id,
            "player_name": _display_name(player.first_name, player.last_name),
            "position": player.position,
            "teams": stat.team_abbreviations.split(",") if stat.team_abbreviations else [],
            "games_played": stat.games_played,
            "goals": stat.goals,
            "assists": stat.assists,
            "shots": stat.shots,
            "hits": stat.hits,
            "blocked_shots": stat.blocked_shots,
            "penalty_minutes": stat.penalty_minutes,
            "plus_minus": stat.plus_minus,
            "power_play_goals": stat.power_play_goals,
            "power_play_assists": stat.power_play_assists,
            "shorthanded_goals": stat.shorthanded_goals,
            "shorthanded_assists": stat.shorthanded_assists,
            "fantasy_points": sum(
                getattr(stat, STAT_COLUMNS[stat_key]) * points
                for stat_key, points in weights.items()
                if stat_key in STAT_COLUMNS
            ),
        }

    ordered = sorted(players.values(), key=lambda entry: (-entry["fantasy_points"], entry["player_name"]))
    return [
        {**entry, "rank": index, "fantasy_points": round(entry["fantasy_points"], 2)}
        for index, entry in enumerate(ordered, start=1)
    ]


def _display_name(first_name: str, last_name: str) -> str:
    return f"{first_name[:1]}. {last_name}" if first_name else last_name


def goalie_rankings(
    session: Session, *, season_id: int, profile: ScoringProfile
) -> list[dict]:
    """Calculate goalie rankings from aggregate goalie season totals."""
    weights = {rule.stat_key: rule.points for rule in profile.rules}
    statement = (
        select(GoalieSeasonStat, Player)
        .join(Player, Player.id == GoalieSeasonStat.player_id)
        .where(GoalieSeasonStat.season_id == season_id, GoalieSeasonStat.game_type == 2)
    )
    players = [
        {
            "player_id": player.id,
            "player_name": _display_name(player.first_name, player.last_name),
            "position": "G",
            "teams": [stat.team_abbreviation] if stat.team_abbreviation else [],
            "games_played": stat.games_played,
            "wins": stat.wins,
            "saves": stat.saves,
            "goals_against": stat.goals_against,
            "shutouts": stat.shutouts,
            "fantasy_points": sum(
                getattr(stat, GOALIE_STAT_COLUMNS[stat_key]) * points
                for stat_key, points in weights.items()
                if stat_key in GOALIE_STAT_COLUMNS
            ),
        }
        for stat, player in session.execute(statement)
    ]
    ordered = sorted(players, key=lambda entry: (-entry["fantasy_points"], entry["player_name"]))
    return [
        {**entry, "rank": index, "fantasy_points": round(entry["fantasy_points"], 2)}
        for index, entry in enumerate(ordered, start=1)
    ]


def all_player_rankings(
    session: Session, *, season_id: int, profile: ScoringProfile
) -> list[dict]:
    """Rank skaters and goalies together using one combined scoring profile."""
    players = player_rankings(session, season_id=season_id, profile=profile) + goalie_rankings(
        session, season_id=season_id, profile=profile
    )
    ordered = sorted(players, key=lambda entry: (-entry["fantasy_points"], entry["player_name"]))
    return [{**entry, "rank": index} for index, entry in enumerate(ordered, start=1)]
