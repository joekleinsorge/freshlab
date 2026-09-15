# Development environment and app scaffolding

## Reproducible shell

Install Nix with flakes and enter the repository environment:

```shell
nix develop
```

With direnv installed, `direnv allow` activates it on repository entry. The
shell includes Ansible, Go, Helm, kubectl, Kustomize, SOPS, age, kubeconform,
linting tools, and pre-commit. It also points `KUBECONFIG` and
`SOPS_AGE_KEY_FILE` at the repository's gitignored local files.

Commit `flake.lock` after first resolving the environment on a machine with Nix.
Subsequent machines should use that lock unchanged.

## Create an application skeleton

```shell
make new-app \
  NAME=example \
  IMAGE=ghcr.io/example/example:1.0.0 \
  PORT=8080 \
  HOSTNAME=example.kleinsorge.dev
```

The generator refuses to overwrite an application. It creates a namespace,
Deployment, Service, HTTPRoute, and default ingress policies. Before committing,
add probes, persistence, authentication, resource sizing, secrets, backup
coverage, monitoring, and a digest-pinned image where supported.
