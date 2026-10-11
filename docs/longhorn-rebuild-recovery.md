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

Manager startup additionally reported that numeric `engine-replica-timeout`
values could not be parsed into the expected map of strings. Helm values now
quote the existing 20-second values so the intended setting can be applied.
