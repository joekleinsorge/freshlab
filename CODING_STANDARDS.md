# Coding standards

Judgement calls a reviewer checks a change against. Mechanical rules are
enforced by tooling instead: pre-commit (`make lint`), digest pinning
(`make validate`), and the CI manifest validation. When a rule here could
become a check, prefer adding the check.

## Placement

- A component lives in the lowest layer that fits: `system/` for
  cluster-critical controllers, `platform/` for shared services, `apps/` for
  user-facing applications. Ordinary applications
  never go in `system/` or `platform/`.
- A new dependency respects the Argo CD sync order: CRDs and Argo CD, then
  SOPS secrets, system, platform, apps. A dependency that runs against that
  order needs the dependency model updated in the same change.

## Following the neighbours

- Match the packaging already used in that area (Helm, Kustomize, or raw
  manifests). Do not convert a component purely for consistency.
- New applications start from `make new-app` or the closest existing app, and
  keep its namespace, Gateway/HTTPRoute, and NetworkPolicy patterns.
- Use Argo Rollouts only where the application already uses progressive
  delivery.
- Reuse existing platform capabilities (Dex for auth, Longhorn for storage,
  VolSync for backup, the existing Gateway) instead of adding a parallel stack.

## Workloads

A normal service has, or the change explains why it does not need:

- readiness and liveness probes
- resource requests and limits that fit a four-node cluster
- a PodDisruptionBudget or priority class where availability matters
- Dex/OIDC authentication when the application supports it
- monitoring or alerting for failure modes someone would need to know about

## State

- A stateful workload has a PVC on an appropriate Longhorn StorageClass,
  VolSync backup coverage, and a recovery path in `docs/operations/backups.md`
  or the app's doc.
- A change to a PVC, StorageClass, Longhorn setting, or backup resource states
  whether it can destroy or orphan existing data, and how that is avoided.
- Stateless workloads do not get backup machinery.

## Versions and secrets

- Charts, images, and vendored dependencies are pinned to explicit versions;
  images by digest. Nothing floats to `latest`. Lock files and vendored chart
  artifacts change with the version.
- No plaintext secret material anywhere outside `freshlab-secrets/*.sops.*`,
  including ConfigMaps, Helm values, scripts, and docs.

## Hosts

- Host configuration changes go through `metal/` Ansible, never a manual step
  documented as the fix.
- Inventory and provisioning logic do not hard-code disk or interface names
  (`/dev/nvme0n1`, `enp2s0`) or historical `192.168.1.x` addresses without
  verifying them.
- The journald limits set by Ansible stay unless the change gives a reason.

## Scope and docs

- A change does one coherent thing; unrelated refactors go in their own commit.
- Comments explain why a non-obvious value was chosen (an incident, a hardware
  limit), not what the YAML says.
- Behaviour an operator would need to know about is reflected in `docs/`, and
  a decision that is hard to reverse has an ADR in `docs/adr/`.
