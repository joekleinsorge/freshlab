# Backups and restores

## Architecture

VolSync snapshots selected Longhorn PVCs every six hours and sends encrypted
Restic repositories to a cluster-internal REST service. The REST service writes
to the existing NAS export at `192.168.1.208:/volume1/kube`, beneath its
`restic/` directory.

Every PVC has its own repository and Kubernetes Secret. Repository encryption,
REST authentication, and the REST server password file are stored as
SOPS-encrypted manifests in `freshlab-secrets`.

The default retention is four hourly, seven daily, four weekly, six monthly,
and two yearly snapshots. The NFS PersistentVolume uses the `Retain` reclaim
policy.

## Check backup health

```shell
make backup-status
kubectl -n restic-rest-server logs deployment/restic-rest-server
```

`LAST` should advance and `RESULT` should report `Successful`. Alerting should
treat a stale `lastSyncTime` as a failed backup even when VolSync is healthy.

## Restore safely

Restores always create a new PVC. They never replace the source automatically.

```shell
make restore \
  NAMESPACE=mealie \
  SOURCE_PVC=mealie-data \
  RESTORE_PVC=mealie-data-restore-20260914 \
  CAPACITY=5Gi
```

After the workflow succeeds:

1. Mount the restored PVC in a temporary pod and inspect it.
2. Stop the application before switching its workload to the restored PVC.
3. Start the application and perform an application-level integrity check.
4. Keep the original PVC until the recovery has been verified.
5. Remove the completed `ReplicationDestination` after closing the recovery.

Database volumes are crash-consistent filesystem snapshots. Add native logical
dumps if transaction-consistent recovery becomes a requirement.

The NAS is off-node, but not independent of itself. Enable NAS snapshots or
replication for `/volume1/kube/restic`.

## Restore drills

The `freshlab-backup-restore-drill` Argo CronWorkflow runs monthly, on the first
at 14:17 America/New_York, using a dedicated ServiceAccount restricted to the
Mealie restore namespace. It restores to a unique disposable PVC, mounts only
that clone in a validation Job, runs SQLite integrity checks, and verifies the
Mealie `recipes` and `users` tables. Its exit handler removes only its uniquely
named Job, ReplicationDestination, and restored PVC. The live PVC is never mounted
or altered by the drill. Failed/aborted workflows run the same cleanup handler.

The GitHub `Verify monthly backup restore drill` workflow independently checks
that the latest drill succeeded and is less than 35 days old. It runs on the
host operations runner with read-only Kubernetes credentials. Trigger an actual
new drill with `scripts/run-restore-drill.py` from an authorized workstation.
Run one after VolSync/storage changes as well as on the monthly schedule.

Important PVCs, required replicas, and maximum backup ages are declared in
`reliability-policy.json`. `scripts/check-cluster-state.py` detects missing,
paused, stale, failed, or incorrectly targeted backup sources. New backup sources
are initially paused until their first backup can be admitted serially during
recovery; a paused required source deliberately fails the health policy. Complete
initial synchronization and commit its unpaused state before claiming coverage.

NAS filesystem snapshots and a second/off-site copy remain external requirements.
Longhorn replicas and local snapshots do not replace those copies. Application
configuration databases, photo libraries on NFS, and off-node etcd snapshots all
need explicit coverage; disposable caches and reconstructible telemetry do not
need the same retention or replica policy.
