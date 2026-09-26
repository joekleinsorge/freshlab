# Freshlab hardware and cluster issue log

Last updated: 2026-09-25 21:25 EDT (NVMe fleet replacement verified; metal1/2/3 confirmed on brand new 512 GB Patriot P300 drives)

This is the running record of confirmed faults, operational risks, and unresolved
symptoms. Update the timestamp and relevant entry whenever an issue is found,
changes state, or is resolved. Do not record credentials or secret values here.

## Active issues

| ID | Area | Severity | Status | Evidence / impact | Current mitigation | Permanent action |
|---|---|---:|---|---|---|---|
| STO-002 | Frigate recording volume / metal0 filesystem alert | High | Recovered; underlying timeout unresolved | On Sep 17 at 07:04 EDT, Longhorn volume `pvc-a401c4d1-0eae-4b94-8107-a45384301578` hit an 8-second R/W timeout to its metal3 replica. The virtual disk `sdf` returned write errors, aborted its EXT4 journal, and remounted read-only. Longhorn salvaged/reattached it as `sdi`; both metal2/metal3 replicas were healthy by 07:29 EDT. At investigation, the volume was writable and new recordings were present. The kernel warned of potentially lost in-flight writes; historical recording integrity was not audited. | Frigate is running and both replicas report RW. All current metal0 EXT4 mounts, including root, are writable. The node's remaining `ReadonlyFilesystem=True` is latched by the detector's permanent log rule, which has no recovery rule. No runtime changes made during investigation. | Investigate replica/network latency before declaring the cause resolved. Metal0 negotiates 1000 Mb/s; its HDD passes SMART with zero pending/reallocated/uncorrectable sectors but is 58°C. Metal3's current Patriot P300 NVMe reports 59°C and zero media errors, while its PCIe root port logged corrected RxErr events around the incident; causation is unproven. Frigate media is 95% full (5.4 GiB available); review retention/capacity. Clear the stale detector condition only after confirming recovery, and consider a mount-aware recovery check. |
| HW-005 | metal0 root HDD / Longhorn | Medium | Upgrade recommended | The node stores about 46 GiB of Longhorn replicas and 18 GiB of K3s data on a Seagate ST500LM034 mechanical HDD. Capacity can be expanded in place, but HDD latency makes this the cluster's slow storage path. SMART tooling is not yet installed, so media age/health is not certified. | Prometheus/Alertmanager monitor disk pressure and capacity. | Prefer a 500 GB-1 TB TLC SSD for the OS and Longhorn data. Until then, install SMART monitoring and avoid making this node the only replica location for important data. |
| HW-006 | metal3 NVMe PCIe link | Critical | Active; cordon before maintenance | The installed Patriot P300 512 GB (Realtek RTS5765DL controller) is SMART-clean (zero media/error-log entries, 3% wear) but recorded 18,051 correctable PCIe physical-layer `RxErr` events on its dedicated root port (`00:1b.0`) during the prior boot. It was 59°C at latest check. This link fault can stall etcd and the node without creating an NVMe media error. | PCIe ASPM is disabled on the next boot, PCIe errors are promoted to a node condition/critical alert, and Kured blocks reboots when storage or node-health alerts fire. | Cordon before hardware work; reseat the M.2, inspect the socket/standoff and airflow, update the Dell OptiPlex 3080 BIOS, then stress-test. Replace the NVMe first, then the board/socket path if RxErr continues. |
| HW-007 | metal2 NVMe operating thermals | Medium | Active | The installed Patriot P300 512 GB NVMe operates at 78°C under sustained load, sustaining the `FreshlabSSDTemperatureHigh` warning alert (>65°C). By comparison, metal1 and metal3 run at 59°C. The drive reports zero media errors, zero critical warnings, and 2% wear. | Alertmanager routes warnings to preventative email. | Inspect chassis fan, clear dust/airflow blockage in the OptiPlex chassis, and fit a low-profile M.2 heatsink. |
| CAP-002 | metal0 root logical volume | Medium | Expansion needed; physical capacity available | The 100 GiB root logical volume has about 19 GiB available while the existing 466 GiB disk's LVM volume group has about 363 GiB free. This is a partitioning/allocation issue, not a need for a larger disk. | Disk-capacity alerts remain active. | Safely extend the root logical volume and ext4 filesystem into the existing free LVM space. |
| NODE-001 | metal3 reachability / controlled reboot | High | Recovered; observe | A Sep 25 reboot was intentionally initiated by Kured after an unattended kernel update created `/var/run/reboot-required`; Kured was configured for a 24/7 window. The node rebooted cleanly. The same prior boot had repeated PCIe RxErr events on the NVMe root port. | Kured is restricted to Sunday 03:00-05:00 EDT and blocks while selected storage or node-health alerts fire. | Complete HW-006 remediation before the next maintenance reboot. If stalls or RxErr recur, keep the node cordoned and replace/migrate the NVMe rather than relying on repeated reboots. |
| STO-001 | Detached Longhorn volume | Low | Investigate | `pvc-182822d0-3756-4a55-a1f1-17b16de27a93` is detached with unknown robustness and has no confirmed active claim. | Left untouched to avoid deleting unidentified data. | Identify its former claim/workload, then retain, recover, or explicitly delete it. |
| APP-002 | Tailscale subnet router | Medium | Blocked externally | The router pod rejects its configured authentication key as invalid and continues restarting. | Core cluster networking does not depend on this pod. | Supply and apply a fresh Tailscale auth key. |

## Recovering / observation

| ID | Area | Status | Evidence / next check |
|---|---|---|---|
| OBS-001 | Prometheus storage | Recovered, watch | A stale read-only Longhorn attachment on metal2 was cleared by moving the healthy 50 GiB volume to metal0. Prometheus recovered its retained WAL. Continue watching for filesystem or Longhorn attachment errors; do not delete the volume merely to accelerate a future startup. |
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
| RES-008 | Prometheus memory and restart loop | Prometheus now prefers 32 GiB metal0, requests 6 GiB, and has an 8 GiB limit. Stakater Reloader excludes the monitoring namespace so generated Prometheus Secrets hot-reload instead of forcing long WAL replays. |
| RES-009 | Monitoring scrape health | Blackbox Exporter is installed; the stale duplicate kubelet service was removed; Longhorn allows Prometheus-only metrics ingress; VolSync metrics no longer return 401; invalid Kindle Weather metrics scraping was removed; and Argo Rollouts was upgraded from v1.0.2 to v1.10.0. |
| RES-010 | Argo CD public DNS | Legacy Argo CD/Workflows Ingresses were removed, their Istio Gateways were pinned to 192.168.1.230 and 192.168.1.229, stale mixed-controller route status was cleared, and ExternalDNS now owns the corrected records. |
| RES-012 | k3s control-plane alerts | Upstream alerts for separately deployed kube-proxy, kube-scheduler, and kube-controller-manager were disabled because k3s embeds these components in its server process. Node, API server, and etcd monitoring remain enabled. |
| RES-013 | NVMe fleet upgrade (metal1/2/3) | All three control-plane nodes were upgraded to brand new 512 GB Patriot M.2 P300 NVMe SSDs (SMART status OK, 0 media errors, 0 critical warnings). Metal1 was returned to scheduling, running etcd and root OS on NVMe (/dev/mapper/ubuntu--vg--1-ubuntu--lv, 465 GiB). |

## Current capacity baseline

| Node | Root disk used | Kubernetes memory used | Scheduling |
|---|---:|---:|---|
| metal0 | about 454 GiB root LV; 363 GiB unallocated in its VG | 29% | Enabled |
| metal1 | 465 GiB root LV on 512 GB Patriot NVMe | 99% allocated requests (settling) | Enabled |
| metal2 | 465 GiB root LV on 512 GB Patriot NVMe | 67% | Enabled |
| metal3 | 465 GiB root LV on 512 GB Patriot NVMe | 35% | Enabled; Ready |

The capacity percentages are point-in-time observations, not guarantees. Grafana
and Alertmanager are the authoritative ongoing view.
