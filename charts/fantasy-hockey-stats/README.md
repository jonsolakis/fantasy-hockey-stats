# Fantasy Hockey Stats Helm chart

This chart deploys the API, static web frontend, and an optional Ingress.
PostgreSQL is provisioned separately by the infrastructure repository so the
database lifecycle is independent of the application release.

## Install

The default values use the published images in your DigitalOcean registry. First
create the Secret that holds the PostgreSQL connection URL:

```sh
kubectl -n fantasy-hockey create secret generic fantasy-hockey-database \
  --from-literal=DATABASE_URL='postgresql+psycopg://USER:PASSWORD@POSTGRES_SERVICE:5432/fantasy_hockey'
```

Then install the chart:

```sh
helm upgrade --install fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey --create-namespace \
  --set database.existingSecret=fantasy-hockey-database
```

For a later app release, override both image tags with the paired immutable
tags you pushed, such as `--set api.image.tag=api-<commit-sha>` and
`--set web.image.tag=web-<commit-sha>`.

Set `ingress.enabled=true` and configure `ingress.hosts` to expose the web
service. The web container proxies `/api` internally, so only the web service
needs to be public.

## Database lifecycle

The Secret named by `database.existingSecret` must contain the
`database.secretKey` key (default: `DATABASE_URL`). The chart does not create
credentials or a database PVC, which keeps secrets and database backups under
infrastructure ownership.

The API pod runs `python -m app.cli migrate` as its first init container before
the application starts. This is safe to rerun, seeds built-in scoring profiles,
and does not require the NHL API.

## Season imports

Season data is not bundled with the chart. When enabled, one CronJob imports
every configured season on the schedule. It runs migrations before each import,
so it is safe for the CronJob to start near an application upgrade. A failed NHL
request retries according to `seasonImport.backoffLimit` but never prevents the
API from serving the last successful snapshot.

```sh
helm upgrade fantasy-hockey ./charts/fantasy-hockey-stats \
  --namespace fantasy-hockey \
  --set database.existingSecret=fantasy-hockey-database \
  --set seasonImport.enabled=true \
  --set seasonImport.seasonIds[0]=20242025 \
  --set seasonImport.seasonIds[1]=20252026
```

Each import replaces that season's aggregate skater and goalie rows, so it is
safe to rerun. To run an import immediately after enabling the CronJob, create
a one-off Job from it:

```sh
kubectl -n fantasy-hockey create job \
  --from=cronjob/fantasy-hockey-fantasy-hockey-stats-season-import \
  fantasy-hockey-season-import-manual
```
