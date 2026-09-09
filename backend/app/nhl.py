"""NHL adapter around the NHL-hosted, undocumented JSON endpoints."""

import httpx

from .providers import (
    GoalieSeasonStatRecord,
    GoalieSeasonStats,
    PlayerSeasonStatRecord,
    SkaterSeasonStats,
)


class NhlClient:
    name = "nhl"
    base_url = "https://api.nhle.com/stats/rest/en"

    def __init__(self) -> None:
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def fetch_skater_season_stats(self, season_id: int, game_type: int = 2) -> SkaterSeasonStats:
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "limit": -1,
            "sort": "playerId",
            "dir": "asc",
            "cayenneExp": f"seasonId={season_id} and gameTypeId={game_type}",
        }
        summary_response = self.client.get(
            "/skater/summary",
            params=params,
        )
        summary_response.raise_for_status()
        summary_records = summary_response.json().get("data", [])

        # NHL splits the fantasy-relevant skater fields between these two reports.
        realtime_response = self.client.get("/skater/realtime", params=params)
        realtime_response.raise_for_status()
        realtime_records = realtime_response.json().get("data", [])
        realtime_by_player_id = {record["playerId"]: record for record in realtime_records}

        return SkaterSeasonStats(
            season_id=season_id,
            game_type=game_type,
            skater_stats=tuple(
                self._normalize_skater(row, realtime_by_player_id.get(row["playerId"], {}))
                for row in summary_records
            ),
            raw_payload={"summary": summary_records, "realtime": realtime_records},
        )

    def fetch_goalie_season_stats(self, season_id: int, game_type: int = 2) -> GoalieSeasonStats:
        response = self.client.get(
            "/goalie/summary",
            params={
                "isAggregate": "false",
                "isGame": "false",
                "limit": -1,
                "sort": "playerId",
                "dir": "asc",
                "cayenneExp": f"seasonId={season_id} and gameTypeId={game_type}",
            },
        )
        response.raise_for_status()
        records = response.json().get("data", [])
        return GoalieSeasonStats(
            season_id=season_id,
            game_type=game_type,
            goalie_stats=tuple(self._normalize_goalie(row) for row in records),
            raw_payload={"data": records},
        )

    @staticmethod
    def _normalize_skater(row: dict, realtime_row: dict | None = None) -> PlayerSeasonStatRecord:
        realtime_row = realtime_row or {}
        teams = row.get("teamAbbrevs") or row.get("teamAbbrev") or ""
        if isinstance(teams, str):
            teams = teams.split(",")
        full_name = row.get("skaterFullName", "").split()
        return PlayerSeasonStatRecord(
            source_player_id=row["playerId"],
            first_name=row.get("firstName") or (full_name[0] if full_name else ""),
            last_name=row.get("lastName") or (full_name[-1] if full_name else ""),
            position=row.get("positionCode", ""),
            team_abbreviation=teams[-1] if teams else "",
            games_played=row.get("gamesPlayed", 0),
            goals=row.get("goals", 0),
            assists=row.get("assists", 0),
            shots=row.get("shots", 0),
            hits=realtime_row.get("hits", row.get("hits", 0)),
            blocked_shots=realtime_row.get("blockedShots", row.get("blockedShots", 0)),
            penalty_minutes=row.get("penaltyMinutes", 0),
            plus_minus=row.get("plusMinus", 0),
            power_play_goals=row.get("ppGoals", row.get("powerPlayGoals", 0)),
            power_play_assists=_point_assists(
                row, "ppAssists", "powerPlayAssists", "ppPoints", "ppGoals", "powerPlayGoals"
            ),
            shorthanded_goals=row.get("shGoals", row.get("shorthandedGoals", 0)),
            shorthanded_assists=_point_assists(
                row,
                "shAssists",
                "shorthandedAssists",
                "shPoints",
                "shGoals",
                "shorthandedGoals",
            ),
        )

    @staticmethod
    def _normalize_goalie(row: dict) -> GoalieSeasonStatRecord:
        teams = (row.get("teamAbbrevs") or "").split(",")
        full_name = row.get("goalieFullName", "").split()
        return GoalieSeasonStatRecord(
            source_player_id=row["playerId"],
            first_name=full_name[0] if full_name else "",
            last_name=row.get("lastName") or (full_name[-1] if full_name else ""),
            team_abbreviation=teams[-1] if teams else "",
            games_played=row.get("gamesPlayed", 0),
            wins=row.get("wins", 0),
            losses=row.get("losses", 0),
            ot_losses=row.get("otLosses", 0),
            saves=row.get("saves", 0),
            shots_against=row.get("shotsAgainst", 0),
            goals_against=row.get("goalsAgainst", 0),
            shutouts=row.get("shutouts", 0),
            save_percentage=row.get("savePct", 0),
        )


def _point_assists(
    row: dict,
    primary_assist_key: str,
    fallback_assist_key: str,
    points_key: str,
    primary_goal_key: str,
    fallback_goal_key: str,
) -> int:
    """Derive special-team assists when the NHL report supplies points only."""
    assists = row.get(primary_assist_key, row.get(fallback_assist_key))
    if assists is not None:
        return assists
    return max(row.get(points_key, 0) - row.get(primary_goal_key, row.get(fallback_goal_key, 0)), 0)
