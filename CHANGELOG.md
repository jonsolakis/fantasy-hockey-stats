# Changelog

All notable user-facing changes are documented here. This project follows the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## [Unreleased]

### Added

- Position filtering for player rankings, including centre, wing, defence, and
  goalie positions available in imported NHL data.

## [0.1.8] - 2026-09-10

### Changed

- Moved application storage from SQLite to externally managed PostgreSQL.
- Moved season imports to an independent CronJob so NHL API outages do not
  prevent the API from starting.
