# Freshlab SOPS Secrets

This directory stores Kubernetes secrets encrypted with SOPS.

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

## Apply all secrets

```bash
cd freshlab-secrets
./apply-all-k8s-secrets.sh
```
