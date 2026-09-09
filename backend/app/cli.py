"""Private operational commands; keep write actions off the public API."""

from __future__ import annotations

import argparse

from .data_migrations import seed_builtin_scoring_profiles
from .database import SessionLocal
from .ingestion import import_goalie_season_stats, import_skater_season_stats
from .nhl import NhlClient
from .schema_migrations import upgrade_schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Fantasy Hockey Stats operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate", help="Upgrade the database schema and seed built-in profiles")
    import_season = subparsers.add_parser(
        "import-season", help="Import or refresh aggregate NHL skater and goalie stats for one season"
    )
    import_season.add_argument("season_id", type=int, help="NHL season ID, for example 20242025")
    args = parser.parse_args()

    upgrade_schema()
    with SessionLocal() as session:
        profiles_added = seed_builtin_scoring_profiles(session)
    if args.command == "migrate":
        print(f"Database schema is current; seeded {profiles_added} built-in scoring profile(s).")
        return
    if args.command == "import-season":
        provider = NhlClient()
        try:
            skater_snapshot = provider.fetch_skater_season_stats(args.season_id)
            goalie_snapshot = provider.fetch_goalie_season_stats(args.season_id)
            with SessionLocal() as session:
                skater_count = import_skater_season_stats(session, provider, skater_snapshot)
                goalie_count = import_goalie_season_stats(session, provider, goalie_snapshot)
            print(
                f"Imported {skater_count} skaters and {goalie_count} goalies "
                f"for season {skater_snapshot.season_id}."
            )
        finally:
            provider.client.close()


if __name__ == "__main__":
    main()
