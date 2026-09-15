# Self-hosted Argo CD MCP

Freshlab includes an optional, read-only MCP endpoint for the in-cluster Argo
CD instance. It is deployed by `system/argocd` at
`https://argocd-mcp.kleinsorge.dev/mcp`.

The endpoint is provided by the open-source
[Argo CD MCP Server](https://github.com/argoproj-labs/mcp-for-argocd). It is
separate from Akuity's hosted Agentic Control Plane and only exposes this
Argo CD instance.

## One-time credential setup

The chart creates an API-only Argo CD account named `mcp`, but credentials are
intentionally not stored in Git. After Argo CD has reconciled the account,
generate a token with an administrator session:

```shell
argocd account generate-token --account mcp --server argocd.kleinsorge.dev
```

Create the Secret in the `argocd` namespace using the generated Argo CD token
and a separate random inbound MCP token:

```shell
kubectl -n argocd create secret generic argocd-mcp-credentials \
  --from-literal=argocd-api-token='<argocd-token>' \
  --from-literal=mcp-auth-token="$(openssl rand -hex 32)"
```

For a fully declarative setup, put the equivalent Secret in the encrypted
`freshlab-secrets` tree instead of running the command above.

The deployment starts in read-only mode. The MCP client must send the inbound
token as `Authorization: Bearer <mcp-auth-token>`; this is different from the
Argo CD API token held by the server.

## Client connection

```json
{
  "mcpServers": {
    "freshlab-argocd": {
      "type": "http",
      "url": "https://argocd-mcp.kleinsorge.dev/mcp",
      "headers": {
        "Authorization": "Bearer <mcp-auth-token>"
      }
    }
  }
}
```

The deployment uses the official `node:20-slim` image and installs the pinned
`argocd-mcp@0.9.0` package at startup. Version 0.9.0 is intentional: earlier
0.8.x releases had an unauthenticated network-listener vulnerability.
