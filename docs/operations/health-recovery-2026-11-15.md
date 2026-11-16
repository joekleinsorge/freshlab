# Health recovery — 2026-11-15

All four nodes were Ready, all 62 Argo applications were Synced and Healthy,
all attached Longhorn volumes were healthy, and all PVCs were Bound. Metal2
remained cordoned from earlier maintenance. The latest monthly disposable
Mealie restore succeeded on November 1.

## Recovered backup

qBittorrent's ReplicationSource had been waiting since November 3 for a CSI
snapshot whose backup status retained an error from that day's outage. The
application remains intentionally scaled to zero; its data and backups are kept.
The existing snapshot content's deletion policy was set to Retain before removing
the failed VolumeSnapshot request. This preserves the existing Longhorn backup.
VolSync created a fresh request and successfully completed a new encrypted
Restic backup at 2026-11-15 21:29 EST. Its normal schedule resumed.

The failed disposable `freshlab-qbittorrent-readonly-check` Pod from the earlier
investigation was removed. It used emptyDir storage and no application PVCs.

## Declarative fixes

- Plex's existing 10 GiB configuration PVC was completely full, despite Git's
  StatefulSet template already requesting 15 GiB. Claim templates are immutable
  and ignored during reconciliation, so they cannot resize an existing claim.
  `apps/plex/pvc.yaml` adopts that exact existing claim and requests 15 GiB using
  its original `longhorn` class. The class supports online expansion, both
  replicas were healthy, and its latest Restic backup succeeded at 17:28 EST.
  No claim, volume, filesystem, or data is deleted or replaced. Pruning and
  application deletion cannot delete this PVC through Argo CD.
- Seerr remains scaled to zero. Its direct public route is removed from the
  gateway inventory to stop advertising a backend that returns HTTP 503. Restore
  the route when enabling the application again; its namespace and data remain.
- The health checker distinguishes Longhorn's deliberately retained, removed
  parent of the live volume head from a real cleanup error. Longhorn 1.13 leaves
  an obsolete blank-image upgrade message on this return path
  ([controller source](https://github.com/longhorn/longhorn-manager/blob/v1.13.0/controller/snapshot_controller.go#L457-L480)).
  The exception requires matching authoritative snapshot and engine state,
  matching desired/current images, and a healthy running engine or a detached,
  stopped engine. Other errors, real upgrades, and purge failures still fail.

After publication, deploy only the host checker and policy with:

```sh
ansible-playbook -i metal/inventories/prod.yml metal/operations.yml --tags host-health-code
```

This tag copies the two declarative health files without reconfiguring the runner
or its credentials. Re-run the host health service, cluster smoke test, and verify
Plex filesystem capacity after Argo reconciliation.

## Observations requiring continued attention

The NAS pool is 89% used, with approximately 3.9 TiB free. Budget, Immich library,
and the Restic server expose the same underlying pool, so their capacity alerts
are correlated. Media and backups were not deleted to clear these alerts.
Metal0's root filesystem was 70% used; historical I/O stalls remain relevant,
although the sampled current disk I/O was idle and all serving workloads were
available. OpenFI's image signature audit still reports a missing signature.
