from app.data_migrations import seed_builtin_scoring_profiles
from app.database import Base
from app.models import ScoringProfile
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload


def test_scoring_profile_migrations_are_idempotent():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        assert seed_builtin_scoring_profiles(session) == 2
        assert seed_builtin_scoring_profiles(session) == 0

        profiles = list(
            session.scalars(select(ScoringProfile).options(selectinload(ScoringProfile.rules)))
        )
        assert {profile.name for profile in profiles} == {
            "Peachy Hockey",
            "Yahoo Default Points League",
        }
        peachy = next(profile for profile in profiles if profile.name == "Peachy Hockey")
        assert {rule.stat_key: rule.points for rule in peachy.rules}["penalty_minute"] == -0.5
