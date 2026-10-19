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
`Healthy`, discovers Gateway API hostnames, and checks every HTTPS endpoint. It also rejects node pressure, missing or stale
backups, insufficient independent replicas for important PVCs, and snapshot errors.
The scheduled workflow expects `kubectl`, `jq`, `curl`, DNS access, and a working
kubeconfig on its self-hosted runner.

## Storage and security benchmarks

The manual RWO and RWX jobs each write and read 1 GiB through Longhorn. The
kube-bench job inspects host k3s configuration and requires privileged access.
These resources sit outside the Argo CD roots and should not be run during an
incident or while storage is constrained.

See [the benchmark runbook](../../test/benchmark/README.md) for commands.

## Checks outside Kubernetes

`metal/operations.yml` provisions an unprivileged `freshlab-ops` GitHub runner and
an independent five-minute systemd health timer on metal0. This avoids relying on
ARC or Kubernetes scheduling to detect an API outage. The worker host is still a
shared physical failure domain; a GitHub-hosted watchdog fails if no successful
hourly smoke check has arrived for two hours.

Provision its narrow API identity without printing credentials:

```shell
python3 scripts/provision-health-reader.py --output /tmp/freshlab-health-kubeconfig.yaml
ansible-playbook -i metal/inventories/prod.yml -u lab metal/operations.yml \
  -e operations_runner_kubeconfig=/tmp/freshlab-health-kubeconfig.yaml
```

The helper verifies that the credential cannot read Secrets or patch Longhorn
volumes. Its controller-generated token is stored encrypted with SOPS; the local
kubeconfig is mode 0600 and must stay outside Git. Regenerate this credential after
a cluster/ServiceAccount rebuild or token revocation. Remove the temporary local
kubeconfig after provisioning. The runner's registration token is short-lived and
never logged. Its service credentials and workspace remain outside the repository.

Only scheduled/manual operational jobs use `[self-hosted, freshlab-ops]`. Run
untrusted pull-request code on GitHub-hosted runners. Health jobs do not receive
cluster administrator access. Keep GitHub failure notifications enabled; the
independent watchdog has no dependency on the homelab API, DNS, or Prometheus.

The host timer publishes `freshlab_host_health_failed` and its last-run timestamp
to the existing node-exporter textfile directory. Inspect failures using
`journalctl -u freshlab-host-health`; Prometheus alerts on failing or missing checks.

## Upgrade gate

Run `make lint`, `make validate`, and `make verify-images`, then render the changed
charts and run health regression tests. The image check verifies linux/amd64
availability for rendered containers, hooks, Argo resource Jobs, and generated
mover arguments. It catches a missing digest even when its syntax is valid.

Before infrastructure upgrades, require a successful current smoke check, recent
backups, two surviving etcd members for maintenance, and capacity to rebuild after
one node loss. Upgrade one critical component/node at a time, verify its functional
recovery and restore path, then observe it for 24 hours before the next unrelated
infrastructure upgrade. Database upgrades need a backup and a tested migration/
rollback plan; do not treat them as routine image replacements.
