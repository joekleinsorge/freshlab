# Freshlab SOPS Secrets

This directory stores Kubernetes secrets encrypted with SOPS. Argo CD renders
the directory with KSOPS and continuously reconciles the decrypted Kubernetes
Secrets. The age identity is seeded once during cluster bootstrap and remains
gitignored.

## Prerequisites

- `sops`
- `age`
- A private age key in `key.txt` (or set `SOPS_AGE_KEY_FILE` to your key path)

The helper scripts auto-use `../key.txt` if `SOPS_AGE_KEY_FILE` is not set.

## Edit a secret

```bash
sops freshlab-secrets/kindle.sops.yaml
```

## Apply one secret

```bash
sops -d freshlab-secrets/kindle.sops.yaml | kubectl apply -f -
```

## Reconcile through GitOps

Commit the encrypted file. The `freshlab-secrets` Argo CD Application detects
the change and reconciles it automatically.

## Recovery: apply secrets manually

The helper remains available for bootstrap recovery or when Argo CD is down.

```bash
cd freshlab-secrets
./apply-all-k8s-secrets.sh
```
