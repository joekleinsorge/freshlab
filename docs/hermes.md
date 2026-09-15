# Hermes

Hermes is deployed as an isolated, single-replica gateway in the `hermes`
namespace. It has a Longhorn data volume, no Kubernetes service-account
token, no Obsidian mount, and no cluster RBAC. Its local terminal backend is
deliberately resource-limited because the agent can execute commands inside
its pod.

Create a Secret named `hermes-env` before using the gateway. At minimum, set
the Telegram variables and dashboard basic-auth credentials:

```sh
kubectl -n hermes create secret generic hermes-env \
  --from-literal=TELEGRAM_BOT_TOKEN='replace-me' \
  --from-literal=TELEGRAM_ALLOWED_USERS='replace-me' \
  --from-literal=HERMES_DASHBOARD_BASIC_AUTH_USERNAME='replace-me' \
  --from-literal=HERMES_DASHBOARD_BASIC_AUTH_PASSWORD='replace-me'
```

Use the repository's SOPS/KSOPS workflow for the persistent version of this
Secret. The dashboard is available at `https://hermes.kleinsorge.dev` after
the Secret exists and the pod has restarted.
