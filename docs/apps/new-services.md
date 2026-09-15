# Paperless-ngx, PairDrop, and Ollama

## Paperless-ngx

Paperless is available at `https://paperless.kleinsorge.dev`. Documents, media,
imports, exports, and its SQLite database use the `paperless-data` Longhorn PVC.
Redis is an ephemeral sidecar and can be rebuilt.

The initial administrator is `admin`. Retrieve its generated password locally:

```shell
make paperless-password
```

Change that password after first login. PostgreSQL is preferable if concurrent
use or database-level recovery becomes important.

## PairDrop

PairDrop is available at `https://drop.kleinsorge.dev`. It is stateless and does
not require a backup. Relay and WebSocket fallback infrastructure remain
disabled until needed.

## Ollama

Ollama remains cluster-internal because its API has no built-in access control:

```text
http://ollama.ollama.svc.cluster.local:11434
```

Models use the `ollama-models` Longhorn PVC. This deployment is CPU-only. Pull a
model from inside the pod, for example:

```shell
kubectl -n ollama exec deployment/ollama -- ollama pull gemma3:4b
```
