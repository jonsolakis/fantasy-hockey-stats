# Fantasy Hockey Stats

A small, self-hosted reference site for exploring how NHL players rank under
different fantasy-hockey scoring systems.

## Architecture

- **API:** FastAPI and SQLAlchemy
- **Database:** SQLite in WAL mode, stored on a persistent volume
- **UI:** SvelteKit
- **Deployment:** one Kubernetes StatefulSet replica with a block-backed PVC

The application stores raw player game results independently from scoring rules.
Changing a scoring profile therefore recalculates rankings without re-importing
the underlying hockey data.

External sources sit behind a `StatsProvider` interface. The current NHL adapter
is only responsible for translating NHL JSON to normalized records; the public
API and database do not expose NHL-shaped payloads. A future source can implement
the same interface without changing ranking or scoring code.

## Development with Docker Compose

```sh
docker compose up --build
```

This starts all local dependencies in containers:

- Frontend: `http://localhost:5174`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

The frontend and API both reload when their source files change. SQLite is stored
in Docker's `hockey_data` volume, so it survives container restarts.

Useful commands:

```sh
docker compose logs -f
docker compose down
docker compose exec api pytest
docker compose exec api ruff check backend
docker compose run --rm migrate
docker compose exec api python -m app.cli import-season 20242025
```

`import-season` is intentionally a private operational command, not an API route.
The public reference site remains read-only even without user authentication.

## Database migrations and seed data

The database schema is versioned with Alembic. Compose runs the `migrate` service
before starting the API, so a new or existing `hockey_data` volume is upgraded
automatically. The first migration is safe for the prototype database created by
earlier versions of the app: it recognizes the existing tables and records the
current revision without replacing data.

For Kubernetes, the Helm chart runs this command as an init container in the
API pod against the same PVC:

```sh
python -m app.cli migrate
```

It is safe to rerun. The command upgrades only unapplied schema revisions and
then seeds the built-in Yahoo Default Points League and Peachy Hockey profiles.
Seed profiles are inserted only when their names are absent, so existing profiles
and user-created profiles are never overwritten.

To remove all local app data as well as containers, run `docker compose down -v`.

## Database notes

Development stores the database in Docker's `hockey_data` volume. Production
should mount the `/data` directory from a single-pod, block-backed PVC. Do not
put a WAL-mode SQLite database on NFS or share it across app replicas.

## Kubernetes release

The production Helm chart is in `charts/fantasy-hockey-stats`. It deploys a
single API replica backed by a ReadWriteOnce PVC, a static web frontend, and an
optional Ingress. The frontend proxies `/api` to the internal API service, so
the API does not need a public Service.

The chart defaults to the published images in the DigitalOcean registry:

```sh
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace
```

For a subsequent app release, override both tags with the immutable tags that
were pushed for its commit: `api-<commit-sha>` and `web-<commit-sha>`.

On every install or upgrade, API-pod init containers apply migrations and any
configured season imports before the API starts. This avoids attaching the
SQLite PVC to separate migration/import Jobs. See the chart README for ingress,
existing-PVC configuration, and season-import settings.
