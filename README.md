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

For Kubernetes, run the same command as a one-off Job against the API's PVC:

```sh
python -m app.cli migrate
```

It is safe to rerun. The command upgrades only unapplied schema revisions and
then seeds the built-in Yahoo Default Points League and Peachy Hockey profiles.
Seed profiles are inserted only when their names are absent, so existing profiles
and user-created profiles are never overwritten. Run this Job before rolling out
the API workload for a schema-changing release.

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

Build and publish both production images, then install the chart with their
repositories and a shared release tag:

```sh
docker build -t ghcr.io/your-org/fantasy-hockey-stats-api:1.0.0 .
docker build -t ghcr.io/your-org/fantasy-hockey-stats-web:1.0.0 ./frontend
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace \
  --set api.image.repository=ghcr.io/your-org/fantasy-hockey-stats-api \
  --set web.image.repository=ghcr.io/your-org/fantasy-hockey-stats-web \
  --set api.image.tag=1.0.0 --set web.image.tag=1.0.0
```

On a new install, an API init container applies migrations. On an upgrade, the
chart runs the same idempotent migration command as a pre-upgrade Job before
the application pods are changed. See the chart README for ingress and
existing-PVC configuration.
