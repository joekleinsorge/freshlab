# Cluster health recovery — 2026-09-21

## Causes and durable fixes

- Namespace labels differed between secrets bootstrap and routing configuration.
  Argo also ignored every namespace label, preventing enforcement of the desired
  GPU/VPN exceptions and non-ambient networking. Keep both declarations consistent;
  the health configuration regression test enforces this contract.
- Authenticated routes skipped namespace creation. Namespace management now applies
  to every route; authenticated apps still have no direct bypass route.
- Workflows without an execution account could not write results. The dedicated
  default executor can only create and patch results in the Argo namespace.
- Obsolete Ingress objects remained after migration to HTTPRoute. Their missing
  load-balancer addresses caused misleading Progressing states. Replacement HTTPS
  routes were verified before removing the legacy definitions.
- Homepage's namespace must be created by the system policy app. The apps project
  deliberately cannot create Namespace resources.
- Tailscale authentication was invalid. Replicas are zero at the user's request.
  Before re-enabling, provide a valid sign-in and verify persisted state.
- Availability alerts cover missing Deployment and StatefulSet replicas, including
  admission failures with no pod and failures hidden by login pages.
- The smoke check aggregates failures, checks workloads and PVCs, skips wildcard
  hostnames, and checks the authenticated MCP path rather than its root path.

## Verification

Run `ruby test/health/config_test.rb`, `python3 test/health/smoke_test.py`,
and `make smoke-test`. Configuration regression checks are part of manifest CI.
HTTP success at a sign-in page does not prove the protected backend is ready;
workload checks are required too.

## Snapshot API upgrades

Longhorn's group snapshot CRDs retained `v1alpha1` as their stored version while
the desired definitions used `v1beta2` for storage. All three resource types were
empty. Recovery added the new versions while retaining the old version, verified
emptiness again, updated stored-version metadata, then applied the desired schema.
No CRDs, snapshots, or volumes were deleted.

Before future CRD upgrades, compare `status.storedVersions` with desired
`spec.versions`. Never remove a stored version without verifying and migrating
existing objects. Non-empty collections need an actual data migration, not merely
a status patch. Follow the [Kubernetes version migration procedure](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definition-versioning/).

## Temporary live controls pending publication

A deny sync window on the platform Argo project is scoped only to Tailscale
(manual sync allowed). This prevents the ApplicationSet from restoring its old
one-replica configuration. After the zero-replica configuration is published and
synced, remove this temporary window and verify replicas remain zero.

Namespace labels, executor RBAC, the workflow default, the example CronWorkflow
account, and Frigate networking were repaired live. Publishing the corresponding
Git changes is required to make those repairs durable.
