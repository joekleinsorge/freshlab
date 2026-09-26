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

The `Quarterly backup restore drill` GitHub Actions workflow restores the
non-production `mealie-data` backup to a unique temporary PVC, waits for the
restore workflow and bound volume, then removes only that labeled restore
destination and temporary claim. It never mounts, stops, or modifies the live
Mealie volume. Run it manually after any VolSync upgrade as well as allowing
the quarterly schedule to run.

The drill proves that the encrypted repository, credentials, VolSync mover,
storage class, and destination volume can complete a restore. It does not
validate application-level data semantics; run an application-specific check
when changing Mealie's schema or backup layout.
