from app.database import Base
from app.ingestion import import_skater_season_stats
from app.models import RawSourcePayload, ScoringProfile, ScoringRule, SkaterSeasonStat
from app.providers import PlayerSeasonStatRecord, SkaterSeasonStats
from app.rankings import player_rankings
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class FakeProvider:
    name = "fake"

    def fetch_skater_season_stats(self, season_id: int, game_type: int = 2) -> SkaterSeasonStats:
        raise NotImplementedError


def test_import_season_is_idempotent_and_rankable():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    snapshot = SkaterSeasonStats(
        season_id=20242025,
        game_type=2,
        skater_stats=(
            PlayerSeasonStatRecord(
                source_player_id=1,
                first_name="Jane",
                last_name="Player",
                position="C",
                team_abbreviation="TOR",
                games_played=82,
                goals=30,
                assists=40,
                shots=200,
            ),
        ),
        raw_payload={"data": [{"playerId": 1}]},
    )

    with Session(engine) as session:
        assert import_skater_season_stats(session, FakeProvider(), snapshot) == 1
        assert import_skater_season_stats(session, FakeProvider(), snapshot) == 1
        assert len(session.scalars(select(SkaterSeasonStat)).all()) == 1
        assert len(session.scalars(select(RawSourcePayload)).all()) == 1

        profile = ScoringProfile(
            name="Test Points",
            rules=[
                ScoringRule(stat_key="goal", points=2.0),
                ScoringRule(stat_key="assist", points=1.0),
            ],
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

        assert player_rankings(session, season_id=20242025, profile=profile) == [
            {
                "rank": 1,
                "player_id": 1,
                "player_name": "J. Player",
                "position": "C",
                "teams": ["TOR"],
                "games_played": 82,
                "goals": 30,
                "assists": 40,
                "shots": 200,
                "hits": 0,
                "blocked_shots": 0,
                "penalty_minutes": 0,
                "plus_minus": 0,
                "power_play_goals": 0,
                "power_play_assists": 0,
                "shorthanded_goals": 0,
                "shorthanded_assists": 0,
                "fantasy_points": 100.0,
            }
        ]
