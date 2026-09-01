# Freshlab hardware and cluster issue log

Last updated: 2026-08-31 20:40 EDT

This is the running record of confirmed faults, operational risks, and unresolved
symptoms. Update the timestamp and relevant entry whenever an issue is found,
changes state, or is resolved. Do not record credentials or secret values here.

## Active issues

| ID | Area | Severity | Status | Evidence / impact | Current mitigation | Permanent action |
|---|---|---:|---|---|---|---|
| HW-001 | metal1 NVMe | Critical | Failed; replacement required | The 128 GB SK hynix BC501 is visible on PCIe but reports a 0-byte namespace. `nvme list`, SMART, and controller-identify commands fail with `Resource temporarily unavailable`; the kernel logged namespace-identify and real filesystem write/journal failures. | The NVMe datastore was removed from `/etc/fstab` and Freshlab automation. K3s and etcd use the surviving root disk. | Replace it with an M.2 2280 NVMe SSD. Reinstall Ubuntu/K3s/etcd on the replacement, burn-in test it, then return metal1 to scheduling. Do not reuse the BC501. |
| HW-002 | metal1 root HDD / etcd | High | Healthy media; unsuitable workload | The active Seagate ST500LM034 500 GB 7200 RPM HDD passes SMART and a new short self-test with zero reallocated, pending, or uncorrectable sectors. It nevertheless has 30,267 power-on hours. Historical I/O averaged about 119-131 ms write latency with 28% I/O wait, and etcd reads took 0.1-10+ seconds until metal1 became `NotReady`. | K3s was recovered and metal1 is `Ready` but cordoned (`SchedulingDisabled`). With metal3 now unreachable, etcd availability depends on metal1 and metal2, increasing the urgency of both node repairs. | Keep the HDD only for secondary/noncritical storage. Do not run etcd or latency-sensitive cluster state on it. |
| HW-003 | metal1 storage cooling | Medium | Active | The Seagate HDD is currently 53°C, has repeatedly reached 60°C, and records 48 over-temperature-limit events. Its specified maximum is 44°C. | Reduced cluster workload by cordoning metal1. | Clean the OptiPlex airflow path, verify its fan and drive mounting, and recheck temperatures after installing the replacement SSD. |
| HW-004 | metal0 Ethernet link | High | Active | The NIC and link partner advertise 1 Gb/s, but the live full-duplex link negotiated at only 100 Mb/s. This constrains Longhorn replication and all node/application traffic. Interface counters show no carrier or transmit errors, so the cable or switch port is the first suspect. | The node remains online; no link reset was forced while it is serving workloads. | Replace/reseat the Ethernet cable and try a known-good gigabit switch port, then confirm `ethtool enp1s0` reports 1000 Mb/s. Replace the NIC only if the fault follows the node. |
| HW-005 | metal0 root HDD / Longhorn | Medium | Upgrade recommended | The node stores about 46 GiB of Longhorn replicas and 18 GiB of K3s data on a Seagate ST500LM034 mechanical HDD. Capacity can be expanded in place, but HDD latency and the 100 Mb/s link make this the cluster's slow storage path. SMART tooling is not yet installed, so media age/health is not certified. | Prometheus/Alertmanager monitor disk pressure and capacity. | Prefer a 500 GB-1 TB TLC SSD for the OS and Longhorn data. Until then, install SMART monitoring and avoid making this node the only replica location for important data. |
| CAP-001 | metal2 root filesystem | Medium | Improved; watch | Root usage dropped from 70% to about 51%, but the 128 GB system NVMe provides limited growth headroom. | Prometheus/Alertmanager disk-capacity and predicted-exhaustion alerts are installed. | Continue reviewing container-image and Longhorn replica growth; replace with a 500 GB-1 TB NVMe during planned maintenance rather than waiting for capacity pressure. |
| CAP-002 | metal0 root logical volume | Medium | Expansion needed; physical capacity available | The 100 GiB root logical volume has about 19 GiB available while the existing 466 GiB disk's LVM volume group has about 363 GiB free. This is a partitioning/allocation issue, not a need for a larger disk. | Disk-capacity alerts remain active. | Safely extend the root logical volume and ext4 filesystem into the existing free LVM space. |
| NODE-001 | metal3 reachability | Critical | NotReady; investigation blocked by SSH authentication | Kubernetes stopped receiving node status at about 20:03 EDT and marks metal3 `NotReady`/unreachable. The host answers SSH but rejects the configured `lab` key, preventing drive, thermal, and service diagnostics. | metal2 remains a healthy etcd voter; metal1 is Ready but cordoned. | Restore `lab` SSH key access or use the console, then inspect K3s/journal, NVMe SMART, temperatures, memory, and the network link before returning the node to service. |
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
| RES-001 | Initial node reachability | All four nodes were rebuilt with Ubuntu 26.04.1 and K3s v1.35.1+k3s1 using the `lab` account. Metal3 later regressed; see NODE-001. |
| RES-002 | Root filesystem capacity | LVM root volumes were expanded: metal1 is 455 GiB; metal2/metal3 are 115 GiB. At the latest check, root usage was metal1 16%, metal2 70%, metal3 54%, and metal0 67%. |
| RES-003 | Node memory | No current memory pressure. Latest available memory was approximately metal1 7.1 GiB, metal2 9.6 GiB, metal3 9.1 GiB, and metal0 25 GiB. |
| RES-004 | Istio/Cilium CNI conflict | Cilium now keeps its custom CNI configuration without overwriting Istio. Cilium, Istio CNI, and ztunnel run on all four nodes. |
| RES-005 | Application routing | Application namespaces are enrolled in Istio ambient mode. Shared Gateway API HTTPRoutes are Accepted with resolved backends and ExternalDNS publishes the Gateway addresses. |
| RES-006 | Observability agents | Grafana Alloy and OpenTelemetry agents run on all four nodes. Loki, Tempo, Grafana, and Alertmanager are operational with persistent storage where applicable. |
| RES-007 | KitchenOwl RWO rollout | Deployment strategy changed to `Recreate`, preventing rolling updates from deadlocking on its single-writer Longhorn volume. |

## Current capacity baseline

| Node | Root disk used | Kubernetes memory used | Scheduling |
|---|---:|---:|---|
| metal0 | about 81% of the 100 GiB root LV; 363 GiB unallocated in its VG | 15% | Enabled |
| metal1 | 16% | 29% | Disabled while HW-001/HW-002 remain open |
| metal2 | 51% | 86% of Kubernetes-allocatable memory | Enabled |
| metal3 | Last known 54% | Unknown while unreachable | NotReady |

The capacity percentages are point-in-time observations, not guarantees. Grafana
and Alertmanager are the authoritative ongoing view.
