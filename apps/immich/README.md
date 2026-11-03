# Immich

Immich is served at <https://photos.kleinsorge.dev>.

## Synology Memories

The `Synology Memories` external library belongs to the existing administrator
configured by `externalLibrary.ownerId` in `values.yaml`. Its import path is
`/media/Memories`, backed by the verified Synology NFS export
`192.168.1.208:/volume1/Media/Memories`. The existing `/media` mount is read-only,
so scans cannot modify or delete originals. Synology `@eaDir`, recycle folders,
and desktop metadata files are excluded.

The PostSync Job checks directory readability using the same read-only NFS
source, creates or reconciles the library through Immich's API, and queues a
scan. Repeated syncs reuse the library and refuse to
remove existing import paths or change its owner. Immich's normal scheduled
external-library scans discover later additions; NFS does not reliably provide
filesystem watcher notifications. A manual scan is also available under
Administration → External Libraries.

The job uses the pinned server image and existing database Secret to bootstrap
a temporary API credential with only library read/create/update permissions.
The credential exists only in memory and as a hash in PostgreSQL, is removed in
`finally`, and is never logged. A retry removes any matching credential left by
an interrupted job. This bootstrap depends on the pinned Immich `api_key` schema
and must be checked when upgrading Immich. Library operations use the API.

No PV, PVC, StorageClass, or source photo files are changed. `/data` remains the
existing writable NFS photo volume for uploads and generated files. PostgreSQL
VolSync backups preserve library configuration and indexed metadata; see
[backup operations](../../docs/operations/backups.md). The NAS originals and
generated files need Synology backup coverage separately. After a database
restore, syncing Immich recreates/reconciles the library and queues a scan;
restoring into a new installation also requires setting the correct admin ID.

Verify reconciliation with:

```sh
kubectl -n argocd get application immich
kubectl -n immich get pods,pvc
kubectl -n immich logs job/immich-external-library  # retained only on failure
```
