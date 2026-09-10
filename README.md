# Fantasy Hockey Stats

A small, self-hosted reference site for exploring how NHL players rank under
different fantasy-hockey scoring systems.

## Architecture

- **API:** FastAPI and SQLAlchemy
- **Database:** PostgreSQL
- **UI:** SvelteKit
- **Deployment:** Kubernetes API and web Deployments backed by PostgreSQL

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

The frontend and API both reload when their source files change. PostgreSQL is
stored in Docker's `postgres_data` volume, so it survives container restarts.

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
before starting the API, so a new or existing `postgres_data` volume is upgraded
automatically. The first migration is safe for the prototype database created by
earlier versions of the app: it recognizes the existing tables and records the
current revision without replacing data.

For Kubernetes, the Helm chart runs this command as an init container in the
API pod:

```sh
python -m app.cli migrate
```

It is safe to rerun. The command upgrades only unapplied schema revisions and
then seeds the built-in Yahoo Default Points League and Peachy Hockey profiles.
Seed profiles are inserted only when their names are absent, so existing profiles
and user-created profiles are never overwritten.

To remove all local app data as well as containers, run `docker compose down -v`.

## Database notes

Compose runs a single PostgreSQL container. In Kubernetes, provision PostgreSQL
as infrastructure (a single-replica StatefulSet with its own PVC is appropriate
for this hobby cluster) and provide the application a Secret containing a
`DATABASE_URL` key. The API has no database volume and may be rolled independently
of PostgreSQL. Take regular logical backups with `pg_dump`.

## Kubernetes release

The production Helm chart is in `charts/fantasy-hockey-stats`. It deploys the
API, a static web frontend, and an optional Ingress. PostgreSQL is deliberately
not bundled into the application chart; provision it from the infrastructure
repository and pass its connection URL by Secret. The frontend proxies `/api`
to the internal API service, so the API does not need a public Service.

The chart defaults to the published images in the DigitalOcean registry:

```sh
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace \
  --set database.existingSecret=fantasy-hockey-database
```

For a subsequent app release, override both tags with the immutable tags that
were pushed for its commit: `api-<commit-sha>` and `web-<commit-sha>`.

On every install or upgrade, the API-pod init container applies migrations before
the API starts. Season imports run separately as a CronJob, so an unavailable
NHL API cannot prevent the API Pod from starting. See the chart README for
database-secret, ingress, and season-import settings.
