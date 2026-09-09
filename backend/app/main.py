from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, union
from sqlalchemy.orm import Session, selectinload

from .data_migrations import seed_builtin_scoring_profiles
from .database import SessionLocal, get_session
from .models import GoalieSeasonStat, ScoringProfile, ScoringRule, SkaterSeasonStat
from .rankings import all_player_rankings, goalie_rankings, player_rankings
from .schemas import (
    PlayerRankingResponse,
    RankingPreviewRequest,
    ScoringProfileCreate,
    ScoringProfileResponse,
    SeasonResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as session:
        seed_builtin_scoring_profiles(session)
    yield


app = FastAPI(title="Fantasy Hockey Stats API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scoring-profiles", response_model=list[ScoringProfileResponse])
def list_scoring_profiles(session: Session = Depends(get_session)) -> list[ScoringProfile]:
    statement = select(ScoringProfile).options(selectinload(ScoringProfile.rules)).order_by(
        ScoringProfile.name
    )
    return list(session.scalars(statement))


@app.post(
    "/api/scoring-profiles",
    response_model=ScoringProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scoring_profile(
    payload: ScoringProfileCreate, session: Session = Depends(get_session)
) -> ScoringProfile:
    existing = session.scalar(select(ScoringProfile).where(ScoringProfile.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="A scoring profile with that name already exists.")

    profile = ScoringProfile(name=payload.name, description=payload.description)
    profile.rules = [ScoringRule(stat_key=rule.stat_key, points=rule.points) for rule in payload.rules]
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@app.get("/api/seasons", response_model=list[SeasonResponse])
def list_seasons(session: Session = Depends(get_session)) -> list[dict[str, int]]:
    season_query = union(
        select(SkaterSeasonStat.season_id),
        select(GoalieSeasonStat.season_id),
    ).subquery()
    season_ids = session.scalars(
        select(season_query.c.season_id).order_by(season_query.c.season_id.desc())
    )
    return [{"season_id": season_id} for season_id in season_ids]


@app.get("/api/rankings", response_model=list[PlayerRankingResponse])
def list_rankings(
    season_id: int,
    profile_id: int,
    player_type: Literal["all", "skater", "goalie"] = "all",
    session: Session = Depends(get_session),
) -> list[dict]:
    profile = session.scalar(
        select(ScoringProfile)
        .options(selectinload(ScoringProfile.rules))
        .where(ScoringProfile.id == profile_id)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Scoring profile not found.")
    ranker = {
        "all": all_player_rankings,
        "goalie": goalie_rankings,
        "skater": player_rankings,
    }[player_type]
    return ranker(session, season_id=season_id, profile=profile)


@app.post("/api/rankings/preview", response_model=list[PlayerRankingResponse])
def preview_rankings(
    payload: RankingPreviewRequest, session: Session = Depends(get_session)
) -> list[dict]:
    """Calculate client-provided rules without modifying shared profiles."""
    profile = ScoringProfile(name="Preview")
    profile.rules = [ScoringRule(stat_key=rule.stat_key, points=rule.points) for rule in payload.rules]
    ranker = {
        "all": all_player_rankings,
        "goalie": goalie_rankings,
        "skater": player_rankings,
    }[payload.player_type]
    return ranker(session, season_id=payload.season_id, profile=profile)
