# Freshlab hardware and cluster issue log

Last updated: 2026-08-31 16:13 EDT

This is the running record of confirmed faults, operational risks, and unresolved
symptoms. Update the timestamp and relevant entry whenever an issue is found,
changes state, or is resolved. Do not record credentials or secret values here.

## Active issues

| ID | Area | Severity | Status | Evidence / impact | Current mitigation | Permanent action |
|---|---|---:|---|---|---|---|
| HW-001 | metal1 NVMe | Critical | Failed; replacement required | The 128 GB SK hynix BC501 is visible on PCIe but reports a 0-byte namespace. `nvme list`, SMART, and controller-identify commands fail with `Resource temporarily unavailable`; the kernel logged namespace-identify and real filesystem write/journal failures. | The NVMe datastore was removed from `/etc/fstab` and Freshlab automation. K3s and etcd use the surviving root disk. | Replace it with an M.2 2280 NVMe SSD. Reinstall Ubuntu/K3s/etcd on the replacement, burn-in test it, then return metal1 to scheduling. Do not reuse the BC501. |
| HW-002 | metal1 root HDD / etcd | High | Healthy media; unsuitable workload | The active Seagate ST500LM034 500 GB 7200 RPM HDD passes SMART and a new short self-test with zero reallocated, pending, or uncorrectable sectors. It nevertheless has 30,267 power-on hours. Historical I/O averaged about 119-131 ms write latency with 28% I/O wait, and etcd reads took 0.1-10+ seconds until metal1 became `NotReady`. | K3s was recovered and metal1 is `Ready` but cordoned (`SchedulingDisabled`). The metal2/metal3 control plane retains quorum. | Keep the HDD only for secondary/noncritical storage. Do not run etcd or latency-sensitive cluster state on it. |
| HW-003 | metal1 storage cooling | Medium | Active | The Seagate HDD is currently 53°C, has repeatedly reached 60°C, and records 48 over-temperature-limit events. Its specified maximum is 44°C. | Reduced cluster workload by cordoning metal1. | Clean the OptiPlex airflow path, verify its fan and drive mounting, and recheck temperatures after installing the replacement SSD. |
| CAP-001 | metal2 root filesystem | Medium | Watch | Root filesystem was 70% used (77 GiB of 115 GiB), the highest current node utilization. | Prometheus/Alertmanager disk-capacity and predicted-exhaustion alerts are installed. | Review container image and Longhorn replica growth before it reaches the alert threshold. |
| STO-001 | Detached Longhorn volume | Low | Investigate | `pvc-182822d0-3756-4a55-a1f1-17b16de27a93` is detached with unknown robustness and has no confirmed active claim. | Left untouched to avoid deleting unidentified data. | Identify its former claim/workload, then retain, recover, or explicitly delete it. |
| APP-001 | Seafile metadata databases | High | Blocked on explicit approval | MariaDB and Memcached are healthy, but `ccnet_db`, `seafile_db`, and `seahub_db` are absent. The app route returns HTTP 500. A raw pre-replacement archive is at `/private/tmp/seafile-mariadb-20260831.tgz`. | Persistent MariaDB storage is enabled; the existing Seafile NFS data was preserved. | With explicit approval, create/import clean schemas or perform a metadata recovery from the archive. |
| APP-002 | Tailscale subnet router | Medium | Blocked externally | The router pod rejects its configured authentication key as invalid and continues restarting. | Core cluster networking does not depend on this pod. | Supply and apply a fresh Tailscale auth key. |

## Recovering / observation

| ID | Area | Status | Evidence / next check |
|---|---|---|---|
| OBS-001 | Prometheus | Recovering | Its healthy 50 GiB Longhorn volume moved from metal1 to metal0. Prometheus is running and replaying its TSDB; readiness remains 1/2 until replay completes. Do not delete the volume or WAL merely to accelerate startup. |
| OBS-002 | Seafile MariaDB volume | Recovered, watch | The new 10 GiB Longhorn volume temporarily degraded after metal1 failed, then rebuilt to healthy. Confirm it stays healthy after the next node maintenance event. |
| OBS-003 | Chassis LED patterns | Unclassified | metal1/2/3 were reported flashing white/orange sequences during initial recovery. No vendor-specific diagnostic mapping or continuing hardware fault has been confirmed from those patterns. Record the machine model and an exact video/pattern if they recur. |

## Resolved issues

| ID | Area | Resolution |
|---|---|---|
| RES-001 | Node reachability | All four nodes now run Ubuntu 26.04.1 and K3s v1.35.1+k3s1 and report `Ready`. SSH automation uses the `lab` account rather than `root`. |
| RES-002 | Root filesystem capacity | LVM root volumes were expanded: metal1 is 455 GiB; metal2/metal3 are 115 GiB. At the latest check, root usage was metal1 16%, metal2 70%, metal3 54%, and metal0 67%. |
| RES-003 | Node memory | No current memory pressure. Latest available memory was approximately metal1 7.1 GiB, metal2 9.6 GiB, metal3 9.1 GiB, and metal0 25 GiB. |
| RES-004 | Istio/Cilium CNI conflict | Cilium now keeps its custom CNI configuration without overwriting Istio. Cilium, Istio CNI, and ztunnel run on all four nodes. |
| RES-005 | Application routing | Application namespaces are enrolled in Istio ambient mode. Shared Gateway API HTTPRoutes are Accepted with resolved backends and ExternalDNS publishes the Gateway addresses. |
| RES-006 | Observability agents | Grafana Alloy and OpenTelemetry agents run on all four nodes. Loki, Tempo, Grafana, and Alertmanager are operational with persistent storage where applicable. |
| RES-007 | KitchenOwl RWO rollout | Deployment strategy changed to `Recreate`, preventing rolling updates from deadlocking on its single-writer Longhorn volume. |

## Current capacity baseline

| Node | Root disk used | Kubernetes memory used | Scheduling |
|---|---:|---:|---|
| metal0 | 67% | 17% | Enabled |
| metal1 | 16% | 64% | Disabled while HW-002 remains open |
| metal2 | 70% | 49% | Enabled |
| metal3 | 54% | 48% | Enabled |

The capacity percentages are point-in-time observations, not guarantees. Grafana
and Alertmanager are the authoritative ongoing view.
