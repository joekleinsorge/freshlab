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

## Progressive delivery

`kindle-weather` is managed as an Argo Rollout using the blue-green strategy.
The public `kindle-weather-service` remains on the active revision while the
next revision is made available through the private
`kindle-weather-preview` Service. After the preview is healthy, Rollouts waits
60 seconds and promotes it automatically, then removes the previous revision
after a 30-second safety delay.

To inspect or control a rollout from a workstation with the Rollouts kubectl
plugin installed:

```shell
kubectl -n kindle-weather port-forward service/kindle-weather-preview 8080:80
kubectl argo rollouts get rollout kindle-weather -n kindle-weather --watch
kubectl argo rollouts promote kindle-weather -n kindle-weather
kubectl argo rollouts abort kindle-weather -n kindle-weather
```

While a new revision is waiting for promotion, the port-forward above serves
the preview revision at `http://localhost:8080`; the public hostname continues
to serve the active revision.
