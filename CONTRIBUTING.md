# Contributing

How changes move from an idea to a reconciled cluster. Review rules live in
[CODING_STANDARDS.md](CODING_STANDARDS.md); agent steering lives in
[AGENTS.md](AGENTS.md).

## Environment

```shell
nix develop        # or `direnv allow` once
make git-hooks     # install pre-commit hooks
```

The shell provides Ansible, Helm, kubectl, Kustomize, SOPS, age, kubeconform,
and the linters. It points `KUBECONFIG` at `metal/kubeconfig.yaml` and
`SOPS_AGE_KEY_FILE` at `key.txt`, both gitignored. See
[docs/development.md](docs/development.md).

## Flow

1. **Spec it in an issue.** Non-trivial work starts as a GitHub issue that
   states the problem, the intended end state, and how to verify it. The
   `to-spec` and `to-tickets` skills write these; `triage` labels them (see
   [docs/agents/](docs/agents/)).
2. **Record decisions.** A choice that is hard to reverse, or that a future
   reader would question, gets an ADR in `docs/adr/`. Shared vocabulary goes in
   `CONTEXT.md`. Both are created on first need by the `domain-modeling` skill.
3. **Change Git, not the cluster.** Edit manifests, charts, Kustomize, or
   Ansible. Live `kubectl`/SSH changes are for diagnosis and emergencies only,
   and must be followed by the matching commit.
4. **Validate locally** before committing:

   ```shell
   make lint                         # pre-commit over every file
   make validate                     # image digest pinning policy
   helm template <release> <chart>   # or `kustomize build <dir>` for what you touched
   ```

   CI (`.github/workflows/validate-manifests.yml`) additionally lints every
   Helm chart, runs `test/health/`, checks Ansible syntax, and validates the
   Renovate config.
5. **Commit to `main`.** Argo CD reconciles from `main`; dependency updates
   arrive as Renovate PRs.
6. **Verify after reconciliation:**

   ```shell
   kubectl get applications -n argocd
   make smoke-test
   ```

   Close the issue with what was verified. Update `docs/` when operational
   behaviour changes, and add an entry to
   [docs/issues-and-remediations.md](docs/issues-and-remediations.md) for
   incidents.

## Commit messages

Conventional Commits with the component as scope, imperative, lowercase, and
describing the outcome rather than the edit:

```text
fix(longhorn): rebuild one replica per node at a time
feat(kyverno): prioritize Plex and Frigate pods
docs: record metal0 storage and hardware findings
chore: pin remaining container images by digest
```

Types in use: `feat`, `fix`, `docs`, `chore`, `deploy` (rolling an app to a new
build), `scale` (resource sizing). Name several components as
`fix(plex,frigate): …`. Reference the issue in the body (`Closes #123`) when
there is one.

## Secrets

Secrets are SOPS-encrypted under `freshlab-secrets/`. Never commit plaintext
credentials, kubeconfigs, or `key.txt`, and do not move secret values into
ConfigMaps, Helm values, scripts, or docs.

## Bare metal

Host changes go through the Ansible roles in `metal/`. Never reinstall more
than one control-plane node at a time; keep two healthy etcd members or a
verified snapshot throughout. See [metal/README.md](metal/README.md).
