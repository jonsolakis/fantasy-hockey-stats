"""Idempotent seed data for built-in scoring profiles.

This deliberately stays separate from Alembic schema migrations. It can run in
every environment without overwriting profiles that a user has already edited.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ScoringProfile, ScoringRule

BUILTIN_SCORING_PROFILES = (
    {
        "name": "Yahoo Default Points League",
        "description": "Yahoo Head-to-Head Points defaults for skaters and goalies.",
        "rules": (
            ("goal", 6.0),
            ("assist", 4.0),
            ("plus_minus", 2.0),
            ("power_play_goal", 2.0),
            ("power_play_assist", 2.0),
            ("shot", 0.9),
            ("blocked_shot", 1.0),
            ("win", 5.0),
            ("goal_against", -3.0),
            ("save", 0.6),
            ("shutout", 5.0),
        ),
    },
    {
        "name": "Peachy Hockey",
        "description": "Peachy Hockey scoring for skaters and goalies.",
        "rules": (
            ("goal", 6.0),
            ("assist", 4.0),
            ("plus_minus", 2.0),
            ("penalty_minute", -0.5),
            ("power_play_goal", 1.0),
            ("power_play_assist", 1.0),
            ("shorthanded_goal", 2.0),
            ("shorthanded_assist", 2.0),
            ("shot", 1.0),
            ("hit", 0.3),
            ("blocked_shot", 1.0),
            ("win", 6.0),
            ("goal_against", -3.0),
            ("save", 0.5),
            ("shutout", 6.0),
        ),
    },
)


def seed_builtin_scoring_profiles(session: Session) -> int:
    """Insert built-in profiles once, preserving existing profile rules."""
    added = 0
    for profile_definition in BUILTIN_SCORING_PROFILES:
        if session.scalar(
            select(ScoringProfile.id).where(ScoringProfile.name == profile_definition["name"])
        ) is not None:
            continue
        session.add(
            ScoringProfile(
                name=profile_definition["name"],
                description=profile_definition["description"],
                rules=[
                    ScoringRule(stat_key=stat_key, points=points)
                    for stat_key, points in profile_definition["rules"]
                ],
            )
        )
        added += 1
    if added:
        session.commit()
    return added
