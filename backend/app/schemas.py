from typing import Literal

from pydantic import BaseModel, Field, field_validator

SCORABLE_STAT_KEYS = frozenset(
    {
        "goal",
        "assist",
        "shot",
        "hit",
        "blocked_shot",
        "penalty_minute",
        "plus_minus",
        "power_play_goal",
        "power_play_assist",
        "shorthanded_goal",
        "shorthanded_assist",
        "win",
        "save",
        "goal_against",
        "shutout",
    }
)


class ScoringRuleInput(BaseModel):
    stat_key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    points: float

    @field_validator("stat_key")
    @classmethod
    def validate_stat_key(cls, value: str) -> str:
        if value not in SCORABLE_STAT_KEYS:
            allowed = ", ".join(sorted(SCORABLE_STAT_KEYS))
            raise ValueError(f"stat_key must be one of: {allowed}")
        return value


class ScoringRuleResponse(ScoringRuleInput):
    id: int

    model_config = {"from_attributes": True}


class ScoringProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    rules: list[ScoringRuleInput] = Field(min_length=1)


class ScoringProfileResponse(BaseModel):
    id: int
    name: str
    description: str | None
    rules: list[ScoringRuleResponse]

    model_config = {"from_attributes": True}


class SeasonResponse(BaseModel):
    season_id: int


class PlayerRankingResponse(BaseModel):
    rank: int
    player_id: int
    player_name: str
    position: str
    teams: list[str]
    games_played: int
    fantasy_points: float
    wins: int | None = None
    saves: int | None = None
    goals_against: int | None = None
    shutouts: int | None = None
    goals: int | None = None
    assists: int | None = None
    shots: int | None = None
    hits: int | None = None
    blocked_shots: int | None = None
    penalty_minutes: int | None = None
    plus_minus: int | None = None
    power_play_goals: int | None = None
    power_play_assists: int | None = None
    shorthanded_goals: int | None = None
    shorthanded_assists: int | None = None


class RankingPreviewRequest(BaseModel):
    season_id: int
    player_type: Literal["all", "skater", "goalie"] = "all"
    rules: list[ScoringRuleInput] = Field(min_length=1)
