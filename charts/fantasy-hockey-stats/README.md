# Fantasy Hockey Stats Helm chart

This chart deploys the API, static web frontend, and a single persistent SQLite
database. It is intentionally a single API replica: SQLite is stored on a
ReadWriteOnce volume and must not be shared between replicas.

## Install

The default values use the published images in your DigitalOcean registry:

```sh
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace
```

For a later app release, override both image tags with the paired immutable
tags you pushed, such as `--set api.image.tag=api-<commit-sha>` and
`--set web.image.tag=web-<commit-sha>`.

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

## Season imports

Season data is not bundled with the chart. The optional import Job uses the
same idempotent CLI command as local development. Keep it disabled in the
normal Helmfile values, then enable it for one Helm run when a season should be
imported or refreshed:

```sh
helm upgrade fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey \
  --set seasonImport.enabled=true \
  --set seasonImport.seasonIds[0]=20242025 \
  --set seasonImport.seasonIds[1]=20252026
```

After the Job completes, set `seasonImport.enabled=false` again before routine
upgrades. The chart creates one Job per season, and each Job replaces that
season's aggregate skater and goalie rows, so it is safe to rerun.
