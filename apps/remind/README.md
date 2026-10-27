# Remind

Remind serves the Kindle highlight library at https://remind.kleinsorge.dev.
The application listens on pod loopback; the Service exposes only OAuth2 Proxy.
Dex grants access to `freshlab-admins` and uses the `remind-sso` static client.
The root ApplicationSet disables namespace creation for Remind: its restricted
namespace is created by `freshlab-secrets`, and the apps project cannot create
cluster-scoped Namespace resources.

The application image is pinned in both the Deployment and Kustomization to the
digest published by `joekleinsorge/remind`. Replace both pins from a new publishing
artifact when upgrading. Keep one replica with the `Recreate` strategy: the JSON
store supports one writer.

## Credentials

SOPS/KSOPS manages `remind-sso`, `ghcr-pull`, and
`remind-data-volsync-restic` through `freshlab-secrets`. The matching Dex client
secret is stored in `dex-secrets`; rotate both sides together. The optional
`remind-sendgrid` secret enables email when it contains `SENDGRID_API_KEY`,
`SENDER_EMAIL`, `RECIPIENT_EMAIL`, and `REMIND_EMAIL_TIME=05:00`.
Email scheduling is disabled unless configured explicitly. Provider acceptance
records delivery separately from reviews; only explicit reviews advance the
rediscovery schedule.

## Import

From the Remind source repository:

```sh
scripts/import-clippings.sh "My Clippings.txt"
```

The importer streams to the running server's loopback API. It merges highlights
without replacing review history. The web UI also supports imports and JSON
export. The library also supports favorites, archive, and personal notes.
Do not run an email CLI or a second writer against the active volume.

## Storage and Recovery

`remind-data` is a new 1 GiB Longhorn claim, retained with Argo CD `Prune=false`.
Creating this deployment does not modify or replace any existing application PVC.
The storage class supplies two replicas. VolSync snapshots it every six hours
at minute 32 (05:32, 11:32, 17:32, and 23:32 UTC) and stores an encrypted repository
on the existing NAS-backed restic service. The reliability policy checks for a
successful backup within eight hours.

For a portable Remind JSON export, choose **Restore backup** in **Your library**.
This merges missing highlights and reviews while preserving existing records.
If a merge is interrupted, `restore-pending.json` journals the pending restore.
Fix any storage failure and restart Remind to complete recovery before writes
resume. Preserve this journal when recovering an interrupted restore.

Use the shared restore workflow to restore to a new claim, inspect the JSON
files, stop Remind, and change the Deployment's claim name before restarting.
Preserve UID/GID 65532. Restore `library.json`, `remind-state.json`,
`email-day.json`, and `delivery-status.json` together when present. The daily
marker prevents duplicate delivery after recovery. Keep the original claim
until application data has been verified. See `docs/operations/backups.md`.

## Verify

```sh
kubectl rollout status deployment/remind -n remind
kubectl get pvc,httproute,replicationsource -n remind
kubectl logs deployment/remind -c remind -n remind
curl -I https://remind.kleinsorge.dev/
```

The public route must redirect unauthenticated requests to Dex. `/healthz`
intentionally bypasses login. Library, export, import, review, and status APIs
remain behind the auth proxy. The Daily email tab and authenticated
`/api/status` endpoint expose persisted delivery outcomes.
