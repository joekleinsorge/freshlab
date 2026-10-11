# Longhorn replica rebuild recovery

On 2026-10-11, application availability and HTTPS checks passed while multiple
Longhorn volumes were degraded. The smoke test now checks replica health as well
as PVC binding. Detached volumes with unknown robustness are normal; faulted
volumes and active volumes without healthy redundancy fail the check.

The recovery found surplus, never-healthy replacement replicas on several nodes.
With one rebuild allowed per node, stopped replacements blocked the volume
controller from refreshing its engine replica address map. The engines retained
references to replicas from an earlier instance manager. Restarting a manager did
not resolve the dependency.

The [Longhorn volume controller](https://github.com/longhorn/longhorn-manager/blob/v1.12.1/controller/volume_controller.go)
waits for all potentially healthy scheduled replicas to be running before
refreshing the engine map. Remove a surplus replacement only after confirming:

- The volume has a running healthy source replica in engine mode `RW`.
- The candidate has never been healthy, is stopped, and is not an engine source.
- Enough replicas remain to meet the configured count after rebuilding.
- The remaining replicas use distinct nodes where required by anti-affinity.

Do not delete a healthy or sole recoverable replica, a PVC, or a replica directory
to clear this condition. Allow the one-per-node rebuild queue to drain and verify
each volume returns to `healthy`; workload readiness alone is insufficient.

FreshRSS's engine also needed its nonexistent failed replica reference removed
and its running replacement reconnected before rebuilding resumed. This was a
temporary recovery operation, not a change to desired replica counts.

The final FreshRSS retry was queued behind an optional 53 GB Prometheus replica.
Prometheus required one replica and retained its healthy `RW` source. Temporarily
disabling balancing on that volume and removing only its never-healthy `WO`
replacement freed the slot. FreshRSS and Autobrr then recovered; the balancing
override was restored to `ignored`. All active volumes were healthy and the full
cluster and 40-endpoint smoke test passed after recovery.

Manager startup additionally reported that numeric `engine-replica-timeout`
values could not be parsed into the expected map of strings. Helm values now
quote the existing 20-second values so the intended setting can be applied.
