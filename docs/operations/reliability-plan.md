# Reliability work — 2026-10-19

Tracking issue: https://github.com/joekleinsorge/freshlab/issues/200

## Acceptance criteria

- All four nodes Ready, with no DiskPressure, MemoryPressure, or PIDPressure.
- Active Longhorn volumes healthy; important PVCs have two independent replicas.
- No stuck snapshot purge or engine upgrade. Root filesystems normally have 30% free.
- Important application backups are less than eight hours old; bulk media less than 26 hours old.
- Scheduled health checks run outside Kubernetes; missing results trigger an independent check.
- A disposable monthly restore verifies both volume recovery and application data.
- Infrastructure upgrades proceed independently, with passing image/manifest checks and a healthy-cluster preflight.

## Work and evidence

- [ ] Recover Frigate media snapshot purge and restore the original ext4 reserve.
- [x] Prepare verified VolSync pins and staggered backup manifests; new sources start paused.
- [ ] Complete initial backups serially and commit each activated source.
- [x] Add backup-age, node-pressure, replica-policy, and stuck-snapshot health checks.
- [x] Add bounded Longhorn snapshot cleanup and storage headroom settings.
- [x] Repair Helm dependency setup and verify rendered images against registries.
- [x] Split infrastructure upgrade batches and document maintenance preflight.
- [x] Establish host-level health checks and independent missing-run detection.
- [x] Complete a disposable restore and application-level verification.
- [x] Publish a priced, compatible storage isolation and migration specification.

## Recovery controls

On metal2, `/dev/mapper/ubuntu--vg-ubuntu--lv` was verified as the mounted root
filesystem. Its ext4 reserved block count was **5,236,352** (4 KiB blocks).
During recovery it was temporarily reduced to 1% (1,242,265 blocks) to provide
Longhorn headroom without deleting data or weakening kubelet eviction thresholds.
Restore the original value with `tune2fs -r 5236352` on that verified device after
snapshot reclamation leaves sufficient free space. This is temporary recovery,
not the desired steady state.

Only metal2's k3s service was restarted after its API stopped reporting node
heartbeats; metal1/metal3 were Ready, the API readiness check passed, and off-node
etcd snapshots were present. Preserve two healthy etcd members throughout.

Frigate media's existing off-node Longhorn backup
`engine-upgrade-20261015-a29808406e36` reports Completed, created October 15.
The only healthy source replica is on metal2. Never delete its replica directory.
The two obsolete snapshots were already marked removed before this recovery.
Use Longhorn's snapshot purge API to coalesce them while preserving live data.

## Physical work

Storage isolation and hardware replacement require compatible parts and physical
installation. Keep the three control-plane members and migrate one node at a time.
Hardware choices and current prices are recorded in the companion hardware spec.

Hardware specification: https://github.com/joekleinsorge/freshlab/issues/201

Validation: fourteen Python health tests, Ruby configuration regressions, four changed
Helm chart lints/renders, server-side operations-manifest dry run, Ansible syntax,
image pinning, rendered-image registry verification, and repository lint passed.
The host runner was provisioned with Ansible and registered online as metal0-ops.
The first published manifest validation runs passed on GitHub. GitOps rollout
is underway; remaining initial backups and storage reclamation are pending.

## Recovery progress

- Immich PostgreSQL 18 now has two healthy replicas on metal1 and metal3, verified
  after the new replica completed rebuilding. The desired count is in policy.
- Metal2 was temporarily cordoned during snapshot coalescing to keep new backup
  movers off its busy disk. Uncordon it after purge/reservation verification.
- The temporary VolSync application skip-reconcile annotation was removed by
  ApplicationSet reconciliation; there is no lasting application hold. The verified
  image pin is now published and reconciled; the controller is Healthy.
- First backups for previously unmanaged sources can be bootstrapped serially
  with `initialize-backups.py --apply --repair-pod-images`. This recovery mode
  replaces only the known unavailable image on a never-started Restic mover Pod;
  it does not restart running movers or modify existing Argo-managed sources.
  Each verified success records the unpaused source in Git. Publish/sync the
  controller fix before relying on future scheduled jobs.
- The existing Frigate media backup metadata was located on the off-node NAS at
  `backupstore/volumes/cd/35/pvc-9c4ef657-d951-439b-8ca1-a29808406e36/backups/backup_engine-upgrade-20261015-a29808406e36.cfg`.

- Workflow `freshlab-restore-drill-x4s2j` succeeded: Restic recovered a disposable
  Mealie volume, SQLite integrity and required application tables passed, and
  the temporary PVC, ReplicationDestination and validation Job were removed.
- Serial activation now publishes one source at a time before Argo sync using
  `initialize-backups.py --apply --publish-activations`. This mode requires
  explicit operator approval to publish; that approval was received for this run.
- Backups and restores use the application file owner, including PostgreSQL
  UID 26/GID 999 and Mealie UID/GID 1001. Capability-free root could not read
  PostgreSQL's private directory or restore Mealie ownership; using the actual
  owner fixed both failures without changing live data permissions.
- Aggregate N+1 memory headroom fails for loss of metal0 during backup activity;
  the hardware spec includes a 16-to-32 GiB metal1 upgrade and current pricing.
