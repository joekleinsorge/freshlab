# Repository Guidelines

## Project Structure & Module Organization
- `metal/` (L0): Ansible playbooks to provision k3s and write `metal/kubeconfig.yaml`.
- `system/` (L1): Cluster-critical Helm charts (e.g., Argo CD, ingress, cert-manager).
- `platform/` (L2): Shared services (Grafana, External Secrets, Dex, etc.).
- `apps/` (L3): User-facing apps, each in its own folder.
- Support: `.github/` (CI), `scripts/` (helper scripts and Go tools), `docs/`.

## Build, Test, and Development Commands
- `pre-commit install`: Install Git hooks defined in `.pre-commit-config.yaml`.
- `make metal`: Provision cluster via Ansible; copies kubeconfig to `~/.kube/config`.
- `make system`: Apply system layer (depends on `metal`).
- `make -C system bootstrap`: Bootstrap Argo CD and ApplicationSets.
- `make clean`: Tear down `metal` hosts and wait for SSH to return.
- Tip: Use `KUBECONFIG=metal/kubeconfig.yaml kubectl get nodes` to verify connectivity.

## Coding Style & Naming Conventions
- YAML: 2-space indent; kebab-case filenames; one resource per file when practical.
- Helm: Pin chart versions; default config in `values.yaml`; prefer declarative Argo sync.
- Shell: POSIX `sh`; keep scripts executable. Go: `gofmt`/`go vet` on `scripts/` when changed.
- Paths: Keep layer directories (`metal/`, `system/`, `platform/`, `apps/`) self-contained.

## Testing Guidelines
- No unit tests; validate infra changes locally:
  - Dry-run: `kubectl apply --server-side --dry-run=client -f <path>` or `helm template <chart>`.
  - Observe: `kubectl get events -A`, `kubectl get appsets -n argocd` after bootstrap.
- CI: Super-Linter, CodeQL (python), and Dependency Review run on PRs.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `ci:`, etc. Scope with folder when useful (e.g., `feat(apps/budget): ...`).
- PRs must include: clear summary, linked issues, impact/risk, and validation notes (commands run, screenshots for UI-facing changes).

## Security & Configuration Tips
- Do not commit secrets. Use External Secrets; avoid inline credentials and private keys.
- DNS/TLS via external-dns and cert-manager; prefer values and annotations over hard-coded domains.
- Run `pre-commit` locally before pushing to catch basic issues.

