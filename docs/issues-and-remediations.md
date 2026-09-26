# Freshlab issue and remediation ledger

Last reviewed: 2026-09-25

This is the consolidated record of issues surfaced in Freshlab task history and
of the Git changes made to correct them. It is an index of *material incidents
and regressions*, not a verbatim changelog: routine dependency upgrades,
bootstrap commits, and formatting-only commits are intentionally excluded.

For hardware evidence and longer-lived risks, see
[hardware-and-cluster-issues.md](hardware-and-cluster-issues.md). For the
September 21 recovery procedure, see
[cluster-health-recovery.md](cluster-health-recovery.md).

## Current state and open follow-up

| Area | State | What remains |
|---|---|---|
| Shared public ingress | **Mitigated; verification pending** | The Istio gateway was evicted during a capacity event and could not reschedule on the remaining eligible nodes. Commit `1bf9f1b` adds a GitOps gateway-infrastructure overlay that tolerates `metal0`'s low-bandwidth taint, so the essential 64 MiB gateway can schedule during control-plane pressure. Confirm a Ready gateway pod and successful external routes after reconciliation before declaring the incident closed. |
| LAN DNS | **Open, external** | UniFi's local DNS override served the stale gateway address `.227` while public DNS served `.228`. Gateway API access required authentication, so correcting the override requires an authorized UniFi session. |
| Frigate storage / metal0 filesystem | **Recovered; root cause open** | The recording volume was recovered after an R/W timeout and read-only remount. Investigate the metal0/metal3 replica path, cable/switch speed, and storage latency before treating it as permanently resolved. |
| Hardware risks | **Open** | Control-plane NVMe drives (metal1/2/3) upgraded to brand new 512 GB Patriot P300 SSDs. Metal0's 100 Mb/s link, metal2 NVMe operating thermals (78°C), and capacity items remain tracked in the hardware log. |
| Seafile metadata recovery | **Blocked by approval** | The Seafile route can still fail because its three metadata databases were absent. The preserved archive must be restored only with explicit approval. |
| Tailscale router | **Blocked externally** | Replicas remain disabled because the prior authentication key was invalid; a fresh authorized key is required before re-enabling it. |

## Incident and fix history

### Cluster foundation, storage, and observability

| Issue | Impact / diagnosis | Completed remediation | Evidence |
|---|---|---|---|
| Cilium and Istio CNI conflicted; telemetry and single-writer workloads did not roll out reliably | Node networking and observability agents were unstable; RWO workloads could deadlock during updates. | Preserved the custom Cilium CNI, corrected collector host metrics/kubelet endpoints, and used safe rollout handling for RWO workloads. | `a523988`, `f6448a7`, `c77a893`, `002d74a`, `24785d8`, `4a5c824`, `37cb053`, `a6025fc`, `a9965c2` |
| Prometheus restart loops, excessive memory pressure, and bad/missing scrape targets | Dashboards and alerts could be incomplete or unavailable. | Moved Prometheus toward the high-memory node, set resource headroom, prevented Reloader-induced restarts, restored probes, extended scrape timeout, and repaired target configuration. | `fbb29a3`, `b8590b8`, `be08a34`, `478ae60`, `332f36f` |
| Grafana showed “No data” across the Freshlab dashboard | A stuck terminating Prometheus pod prevented the StatefulSet from coming up, despite Grafana/exporters being healthy. | Recovered the Prometheus workload while retaining its bound PVC; the task later verified Prometheus `2/2 Running` and queries returning data. | Task: **Inspect Freshlab Grafana dashboard**; existing recovery record `OBS-001` |
| Grafana datasource collisions and dashboard fragmentation | Datasource provisioning could select multiple defaults; dashboards were hard to navigate. | Consolidated the datasource provisioner, allowed migrations, aligned retained configuration, and replaced/organized dashboards. | `7667b55`, `3d6e5b6`, `0eb5ff5`, `a6d4c6f`, `138601b`, `70f1dc7`, `a24379c` |
| Node health and storage faults | Metal1's NVMe failed; metal3 suffered slow-disk/restart symptoms; metal0 had a 100 Mb/s link and a Frigate volume timed out/remounted read-only. | Upgraded all control-plane nodes (metal1/2/3) to brand new 512 GB Patriot P300 NVMe SSDs; returned metal1 to scheduling with root and etcd on NVMe; persisted storage diagnostics, added node observability, moved critical workloads away from constrained capacity, and increased Frigate headroom/placement. Metal0 link speed and metal2 thermals remain tracked. | `9e79c70`, `fa63b13`, `0ab89d8`, `2fb7d85`, `5cc6b62`, `ba908a4`; hardware log `HW-001`–`HW-007`, `STO-002`, `RES-013` |

### GitOps, routing, and platform control plane

| Issue | Impact / diagnosis | Completed remediation | Evidence |
|---|---|---|---|
| Legacy Ingresses conflicted with Gateway API/ambient routing | Routes carried stale or missing load-balancer state, and ExternalDNS could publish incorrect targets. | Removed conflicting legacy Ingresses, centralized routes on the shared Gateway, pinned specific gateway targets where needed, and normalized controller-owned fields. | `7fbeee2`, `484d1b2`, `5afda30`, `a84499e`, `cbd5441`, `d40caab` |
| Argo CD could not consistently render or reconcile applications | Missing vendored Helm dependencies, missing KSOPS access, controller memory exhaustion, generated-app sync settings, and controller-managed drift blocked reconciliation. | Vendored chart dependencies, exposed KSOPS, increased controller capacity, enabled generated/static app sync, and added targeted drift ignores. | `bdbcbae`, `42ba13b`, `c08629f`, `df49588`, `83c7dfe`, `a974485`, `da6262c`, `975108e`, `fd65332` |
| Argo Rollouts routing could be lost during sync | Service routing changed unexpectedly during GitOps reconciliation. | Made controller replacement one-time, set the Rollouts dashboard/migration correctly, and preserved service routing. | `19c54c3`, `a6eb50e`, `6e3925e` |
| Argo sample workflow overloaded etcd/control-plane capacity | Repeated per-minute runs contributed avoidable control-plane load. | Removed the runaway workflow and corrected Argo controller scheduling/capacity. | Recovery task summary; `fd65332` |
| Namespace ownership, labels, and ambient-mesh policy disagreed | Required namespaces were not consistently created/labeled; exceptions for GPU/VPN and health-probe routing could not be enforced. | Reconciled policy/gateway ownership, labeled secret-owned namespaces for ambient mode, excluded probe-sensitive apps, and documented regression tests. | `4479bd8`, `091fc9f`, `6ea0d91`; [cluster health recovery](cluster-health-recovery.md) |
| Longhorn snapshot CRD version mismatch | Stored `v1alpha1` versions conflicted with desired `v1beta2` storage versions. | Retained the old version until empty resources and stored-version metadata were verified, then converged the schema without deleting data. | `2d7fa10`; [cluster health recovery](cluster-health-recovery.md) |

### Media, authentication, and application workloads

| Issue | Impact / diagnosis | Completed remediation | Evidence |
|---|---|---|---|
| Plex GPU, transcoding, optimized versions, and PVC expansion issues | GPU allocation/permissions blocked transcode verification; an immutable claim template and storage expansion required careful handling. | Corrected device allocation and smoke permissions, added backup/transcode safeguards, allowed optimized media versions, ignored immutable claim-template drift, and restarted Plex after PVC expansion. | `bf0ef9f`, `1c8097d`, `6abb6b1`, `bdd0953`, `cbc625f`, `a7eb2a3` |
| Plex configuration backup failures | Restic credentials/repository paths and user permissions were wrong; stale locks and jobs blocked new VolSync runs. | Repaired credentials and repository isolation/paths, ran backups as the Plex user, avoided repeated ownership scans, and removed stale Restic locks/failed jobs during recovery. | `028fc05`, `b4da4c3`, `d7d6b1c`, `afb3f49`, `19f5a72`; tasks **Check Plex health and usage** and **Check cluster and app health** |
| Plex “changes could not be saved” | The Plex library-folder change failed through the deployed instance. | The task history records continued live investigation and later health checks; durable related fixes cover Plex storage/backup/GPU safeguards. A single final causal commit for the UI save error was not identified, so this item should remain a symptom reference rather than a claimed closed fix. | Task: **Fix Plex library save error** |
| Media OIDC gateway failed health checks or callbacks | Protected apps could not reach the gateway correctly; cross-subdomain login flow failed. | Made health checks reachable, set the health-probe host, restarted configuration changes, allowed cross-subdomain callback and protected-app reachability, and declared route defaults. | `6880b97`, `2c3db44`, `6ad8f17`, `f6f14cf`, `ad1e375`, `20fe28e`, `d7afed2` |
| Immich, Seafile, and Frigate experienced application/storage/probe faults | Workloads were unhealthy or inaccessible after storage/network changes. | Recovered Immich and mounted media; restored Seafile data/cache/probes and rebuilt shared data on Longhorn; repaired Frigate ingress/static paths, MQTT, persistence, capacity, retention, and probe merge behavior. | `fde9dfd`, `5826231`, `164cccd`, `32dc001`, `b70bc77`, `50cd3c6`, `9a0f1fe`, `0a6f354`, `ca24548`, `8ab8807`, `ba908a4` |
| qBittorrent and PairDrop deployment defects | qBittorrent used a wrong/unsupported network or export; PairDrop required init privileges. | Used the existing media NFS export and PIA OpenVPN/Gluetun configuration; allowed LinuxServer init privileges. Retired PairDrop was subsequently removed from GitOps. | `417cc8a`, `7433490`, `4041881`, `aa81c98`, `f4e7916` |
| RomM used nonportable host-path storage | The workload was not portable/recoverable across nodes. | Replaced host paths with persistent storage. | `1441e76` |
| Recyclarr replayed stale outage jobs | Historical failures kept producing degraded/outage signals. | Prevented stale failures from being replayed and corrected the namespace bootstrap. | `61abe54`, `1b5a7d2` |

### Security, secrets, and access

| Issue | Impact / diagnosis | Completed remediation | Evidence |
|---|---|---|---|
| App secrets were inconsistently managed/encrypted | Apps and dashboards could miss secrets; Disney Alerts SOPS metadata/data format was invalid. | Replaced external-secrets usage with SOPS-managed app secrets, wired dashboard/Recyclarr secrets, repaired and re-encrypted Disney metadata while preserving encrypted data format. | `038c2be`, `10c1cb5`, `b28f9b8`, `2667a17`, `54062e5` |
| Dex/OIDC login paths failed for Argo, media, Hermes, and Disney Alerts | CLI callback/client visibility and web login could fail. | Marked the Argo CLI client public, allowed its callback, enabled media/Hermes login routes, pinned compatible OIDC images, and added the Disney Alerts client. | `4b6ffc5`, `59b2914`, `003d32f`, `77b2755`, `86f11d7`, `e642f8d` |
| Argo Workflows could not access its SSO secret or write results | Workflows failed before or during result reporting. | Granted SSO secret access and configured a least-privilege default executor. | `ede140a`; [cluster health recovery](cluster-health-recovery.md) |

### Alert quality, DNS, and operations

| Issue | Impact / diagnosis | Completed remediation | Evidence |
|---|---|---|---|
| Alert email was too noisy | Warning/info and resolved messages obscured actionable incidents. | Restricted email to sustained critical alerts, suppressed warning/info and resolved emails, grouped alerts, and limited repeats. | `427a8e6`; task **Reduce unnecessary alerts** |
| Duplicate/low-value alerts and Immich probe instability | Operators received redundant notifications and unreliable health signals. | Reduced duplicate alerts, stabilized Immich probes, removed obsolete collector metrics, and documented the workload/PVC-aware smoke check. | `bcc61ff`, `37b30ed`, `d22ddba`; [cluster health recovery](cluster-health-recovery.md) |
| ExternalDNS did not consistently publish the active shared-gateway address; the public gateway was later evicted and unschedulable | Public records could point at a stale/nonfunctional ingress; when the gateway pod was evicted, every public app at the shared address was unavailable. | Switched to the active annotation prefix, published DNS at gateway scope, hardened DNS/node-filesystem monitoring, aligned ingress inventory to the gateway address, and added an Istio infrastructure overlay so the essential gateway can tolerate metal0 during control-plane pressure. | `5205813`, `76eee61`, `2f3cd01`, `57d07a6`, `1bf9f1b` |
| System DaemonSets and Longhorn updates increased risk on constrained nodes | Essential agents could be unschedulable or Longhorn managers could roll simultaneously. | Allowed essential system DaemonSets on the low-bandwidth node and configured sequential Longhorn manager rollouts. | `7d84e6c`, `27b3c69` |
| VolSync secret bundle emitted empty YAML documents and retained an obsolete Ollama secret | GitOps rendering could fail or retain retired configuration. | Filtered empty documents and removed the stale Ollama VolSync secret/source. | `b42a529`, `523020e`, `3108f99` |

## How this ledger was assembled

- Reviewed all currently listed Freshlab project tasks plus the two task threads
  whose working directory is Freshlab. The task titles used as direct evidence
  are: **Investigate and resolve alerts**, **Fix Plex library save error**,
  **Inspect Freshlab Grafana dashboard**, **Reduce unnecessary alerts**,
  **Check Plex health and usage**, **Check cluster and app health**, and
  **Troubleshoot Plex Freshlab**.
- Reviewed the repository's full reachable Git history. Commit references above
  are short hashes and can be inspected with `git show <hash>`.
- Did not treat a task title or a commit beginning with `fix:` as proof by
  itself. Where a final verified outcome was absent, the entry is explicitly
  marked open, in progress, blocked, or symptom-only.

## Operating rule

When an incident is discovered, add it to the hardware log if it is a
long-lived risk; add or update an entry here when a durable Git change is made.
Record the triggering evidence, the deployed commit, verification performed,
and any condition that prevents declaring the incident resolved. Never include
credentials, access keys, or decrypted secret values.
