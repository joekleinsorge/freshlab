# ADR 0001: Isolate Longhorn storage from control-plane disks

Date: 2026-10-19
Status: Accepted design; hardware procurement and installation pending
Tracking: https://github.com/joekleinsorge/freshlab/issues/200

## Context

Repeated disk-pressure and I/O incidents have affected etcd, Longhorn, and serving
applications together. All three control-plane members currently share one
physical disk between etcd, root/image storage, and Longhorn. Frigate snapshot
growth on metal2 can consume most of that disk despite a much smaller nominal PVC.

## Decision

Preserve the three-member embedded-etcd k3s topology. Give Longhorn a separate
internal SSD on storage-participating hosts, keep root/etcd on a reliable NVMe
device, and require UUID-based mount guards. Budget actual physical consumption,
snapshot maintenance, and one-host failure headroom. Important PVCs require two
independent replicas and off-node backup coverage; disposable data has explicit
lower requirements. Use existing Longhorn, VolSync, Argo, and host Ansible tooling.

## Consequences

Requires compatible drives, installation, and sequential migration. It isolates
capacity and device I/O, but shared power, chassis, switch, and NAS failures remain.
Extra replicas are admitted only when recovery capacity exists. Monitoring and
restore drills provide evidence of recoverability. See the
[priced hardware specification](../operations/storage-hardware-spec.md).
