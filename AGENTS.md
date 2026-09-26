# AGENTS.md

Freshlab is a personal GitOps-managed k3s homelab. Treat this repository as the source of truth for persistent infrastructure and Kubernetes configuration.

## Repository Structure

```text
metal/      Bare-metal Ubuntu configuration, Ansible, and k3s provisioning
bootstrap/  Initial GitOps/bootstrap configuration
system/     Cluster-critical controllers and infrastructure
platform/   Shared services used by applications
apps/       User-facing/self-hosted applications
global/     External/public-facing services
docs/       Architecture and operational documentation
scripts/    Cluster management and validation utilities
test/       Configuration, health, storage, and security tests
```

Place new components in the lowest appropriate layer. Do not put ordinary applications in `system/` or `platform/`.

## Core Architecture

- OS: Ubuntu Server 26.04 LTS, amd64
- Kubernetes: k3s
- Cluster:
  - `metal1`, `metal2`, `metal3`: control-plane/etcd
  - `metal0`: worker
- GitOps: Argo CD
- Progressive delivery: Argo Rollouts
- Workflows: Argo Workflows
- Secrets: SOPS + KSOPS + Age
- Identity: Dex/OIDC
- Storage: Longhorn
- Backups: VolSync/restic to off-node storage
- Primary domain: `kleinsorge.dev`

Preserve the three-member control-plane topology unless explicitly redesigning the cluster.

## Source of Truth

Persistent changes belong in Git.

Do not use live cluster changes as the final solution when the configuration is managed by this repository.

For host configuration managed by Ansible, modify the Ansible role/playbook rather than relying on manual SSH changes.

For Kubernetes configuration, modify manifests/charts/Kustomize configuration and allow Argo CD to reconcile them.

Temporary live changes are acceptable for diagnosis, recovery, or emergency mitigation, but the intended state must subsequently be represented in Git.

## GitOps Ordering

The root Argo CD ApplicationSet uses progressive synchronization.

Expected order:

1. Argo CD and required CRDs
2. SOPS-managed Secrets
3. Remaining system controllers
4. Platform/shared services
5. User applications

Do not introduce dependencies that violate this ordering without updating the dependency model.

## Secrets

Never commit plaintext credentials, tokens, passwords, private keys, kubeconfigs, or Age identities.

Kubernetes secrets belong in the separate `freshlab-secrets` repository and are encrypted with SOPS.

The local `key.txt` Age identity is bootstrap material and must remain uncommitted.

Do not move secrets into ConfigMaps, Helm values, environment files, documentation, or shell scripts.

## Bare-Metal Safety

Do not reinitialize or reinstall multiple control-plane nodes simultaneously.

Maintain either:

- at least two healthy etcd members, or
- a verified etcd snapshot

during control-plane maintenance.

Do not assume disk or network interface names. Verify them before changing inventory or provisioning logic.

Typical hardware currently uses:

```text
/dev/nvme0n1
enp2s0
```

but these are not guaranteed.

## Storage

Assume important stateful workloads need:

- a persistent volume
- appropriate Longhorn configuration
- backup coverage
- a documented recovery path

Before changing PVCs, StorageClasses, Longhorn configuration, or backup resources, determine whether the change can destroy or orphan existing data.

Stateless workloads do not need unnecessary backup machinery.

## Networking

Do not assume historical `192.168.1.x` addresses are current.

Use repository configuration and live state when diagnosing:

- Gateway/Ingress
- DNS
- LoadBalancer addresses
- UniFi static DNS
- public DNS
- service routing

Prefer existing networking patterns over introducing a parallel ingress or service-mesh solution.

## Authentication

Dex is the shared OIDC provider.

Prefer integrating supported applications with the existing OIDC setup instead of creating independent local authentication systems.

Preserve break-glass administrator access until replacement authentication has been tested.

## Application Conventions

Before adding or significantly changing an application, inspect similar existing applications.

The repository intentionally uses a mixture of:

- Helm
- Kustomize
- raw Kubernetes manifests

Follow the existing pattern for that area instead of rewriting components solely for consistency.

For a normal service, consider:

- namespace
- workload
- Service
- Gateway/Ingress
- TLS/DNS
- persistent storage
- backup requirements
- monitoring
- NetworkPolicy/security
- probes
- resource requests/limits
- GitOps health behavior

Use Argo Rollouts where an application already uses progressive delivery.

## Dependency Pinning

Prefer explicit and reproducible versions.

Do not replace pinned Helm charts, image digests, or vendored dependencies with floating versions such as `latest`.

When updating dependencies, update lock files or vendored chart artifacts as required.

## Validation

Run the relevant repository validation before considering a change complete.

Common checks include:

```bash
make lint
make validate
```

and existing tooling under:

```text
scripts/
test/health/
test/benchmark/
```

Also render Helm/Kustomize output when modifying manifests or charts.

For changes affecting the live environment, verify cluster health after reconciliation.

Typical checks:

```bash
kubectl get nodes -o wide
kubectl get applications -n argocd
kubectl get pods -A
kubectl get events -A
```

Use existing smoke tests when applicable.

Do not disable validation merely to make a change pass.

## Troubleshooting

Investigate from lower layers upward:

```text
host
→ k3s
→ networking/CNI
→ storage
→ Argo CD
→ system
→ platform
→ application
→ ingress/DNS
```

Inspect logs, events, resource health, disk space, and node status before rebuilding or deleting resources.

Useful host checks:

```bash
systemctl status k3s
journalctl -u k3s
df -h
df -i
free -h
lsblk
ip -br addr
```

Host journald limits are intentionally managed by Ansible:

```ini
Storage=persistent
SystemMaxUse=200M
RuntimeMaxUse=100M
```

Do not undo these without a specific reason.

## Change Philosophy

Prefer:

- durable root-cause fixes
- declarative configuration
- reproducibility
- automation
- simple recovery
- low maintenance
- existing platform capabilities
- appropriate observability and security

Avoid:

- manual configuration drift
- unnecessary enterprise complexity
- duplicate infrastructure stacks
- large unrelated refactors
- changing architecture solely for stylistic consistency

A four-node homelab should remain understandable and maintainable.

## Agent Workflow

For any non-trivial change:

1. Read the relevant current files.
2. Inspect nearby implementations for conventions.
3. Identify the correct architecture layer.
4. Understand dependencies and stateful-data impact.
5. Make the smallest coherent declarative change.
6. Update tests/documentation when behavior changes.
7. Run relevant validation.
8. Review the final diff for accidental secrets or unrelated changes.

Do not infer current infrastructure values from old documentation when the repository or live cluster can provide them.

## Important References

Start with:

```text
README.md
docs/
docs/gitops-operations.md
metal/README.md
metal/Makefile
metal/inventories/prod.yml
system/argocd/
scripts/cluster-smoke-test
test/health/
```

For any disagreement between documentation and implementation, inspect current code and configuration before changing behavior.
