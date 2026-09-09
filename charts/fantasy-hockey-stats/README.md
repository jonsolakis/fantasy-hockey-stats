# Fantasy Hockey Stats Helm chart

This chart deploys the API, static web frontend, and a single persistent SQLite
database. It is intentionally a single API replica: SQLite is stored on a
ReadWriteOnce volume and must not be shared between replicas.

## Install

Build and publish the two images first, then provide their repositories and tag:

```sh
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace \
  --set api.image.repository=ghcr.io/your-org/fantasy-hockey-stats-api \
  --set web.image.repository=ghcr.io/your-org/fantasy-hockey-stats-web \
  --set api.image.tag=1.0.0 \
  --set web.image.tag=1.0.0
```

Set `ingress.enabled=true` and configure `ingress.hosts` to expose the web
service. The web container proxies `/api` internally, so only the web service
needs to be public.

## Database lifecycle

The API init container runs `python -m app.cli migrate` for a new installation.
On upgrades, the chart runs the same idempotent command as a Helm pre-upgrade
Job before the API workload is changed. The PVC is retained by Helm by default;
uninstalling the release does not delete it automatically.

Use `persistence.existingClaim` to point at an existing ReadWriteOnce claim.
Never increase `api.replicaCount` above one while using SQLite.
