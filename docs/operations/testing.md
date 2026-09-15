# Testing and benchmarks

## Repository validation

The validation workflow renders and lints Helm charts, checks Ansible syntax,
validates Renovate configuration, and rejects obvious plaintext secrets.
Supply-chain workflows add vulnerability, configuration, SBOM, and dependency
checks.

## Live smoke test

Run this from a machine with cluster credentials and Freshlab DNS access:

```shell
make smoke-test
```

It waits for all nodes, requires every Argo CD Application to be `Synced` and
`Healthy`, discovers Gateway API hostnames, and checks every HTTPS endpoint.
The scheduled workflow expects `kubectl`, `jq`, `curl`, DNS access, and a working
kubeconfig on its self-hosted runner.

## Storage and security benchmarks

The manual RWO and RWX jobs each write and read 1 GiB through Longhorn. The
kube-bench job inspects host k3s configuration and requires privileged access.
These resources sit outside the Argo CD roots and should not be run during an
incident or while storage is constrained.

See [the benchmark runbook](../../test/benchmark/README.md) for commands.
