# GitOps Operations

## Secrets

All Kubernetes Secret manifests live in `freshlab-secrets` as SOPS-encrypted
files. Argo CD renders that directory through KSOPS and reconciles it before
the rest of the platform and application layers.

The local, gitignored `key.txt` is the bootstrap identity. `system/bootstrap.yml`
copies it to the `argocd/sops-age` Secret before Argo CD starts; do not commit
that file. If Argo CD is unavailable, use `freshlab-secrets/apply-all-k8s-secrets.sh`
only as a recovery measure.

## Deployment order

The root ApplicationSet uses progressive syncs:

1. Argo CD and Gateway API CRDs.
2. SOPS-managed Secrets.
3. Remaining system controllers.
4. Shared platform services.
5. User-facing applications.

Each layer must become Healthy before the next one starts. System workloads
remain trusted to manage cluster-scoped resources; platform and apps are
restricted by dedicated AppProjects.

## Access

Dex is the shared OIDC provider for Grafana, Argo CD, and Argo Workflows.
The built-in Dex administrator belongs to `freshlab-admins`; Argo CD maps that
group to the admin role while all other authenticated users are read-only.
Argo Workflows uses the same group for its administrative service account.

Keep the Argo CD local administrator enabled as break-glass access until an
interactive OIDC login to both Argo CD and Argo Workflows has been verified.
After that verification, set `argo-cd.configs.cm.admin.enabled: false`.

## Operational workflows

The `argo-workflows-ops` application provides cluster-scoped templates:

- `freshlab-cluster-readiness` waits for nodes and Argo CD Applications to be
  Healthy.
- `freshlab-http-smoke` checks an explicitly supplied HTTP URL and status.

Both run with a dedicated read-only ServiceAccount. Workflow creation remains
limited to the Argo Workflows administrative group.
