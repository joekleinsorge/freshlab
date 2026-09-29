# Plex remote access

Plex's Service requests `192.168.1.231` from the existing Cilium load-balancer
pool (`192.168.1.224/27`). The cluster uses Cilium LB IPAM, not MetalLB.
`192.168.1.229` is already allocated to the Argo Workflows gateway.

The `plex` LoadBalancer Service exposes TCP `32400` and retains its internal
ClusterIP for the existing Istio route. `plex.kleinsorge.dev` continues through
the shared HTTPS gateway at `192.168.1.228`. The direct-access NetworkPolicy
permits inbound TCP `32400` to Plex from LAN and remote clients.

## Deployment and verification

1. Publish the manifests through the normal GitOps workflow and wait for the
   `plex` Argo CD application to reconcile. Check that
   `kubectl -n plex get svc plex` reports external IP `192.168.1.231` and
   port `32400/TCP`.
2. Wait for Plex's database migrations to finish before testing access. A
   Running pod alone does not establish that migrations are complete.
3. From the LAN, open `http://192.168.1.231:32400/web/`. Also verify that
   `https://plex.kleinsorge.dev/web/` still works through Istio.
4. In UniFi, update the Plex port forward to WAN TCP `32400` →
   `192.168.1.231:32400`. Remove or disable the old forward to the NAS at
   `192.168.1.208`. Do not forward this port to the shared gateway `.228` or
   the Argo Workflows gateway `.229`.
5. In Plex Settings → Remote Access, enable **Manually specify public port**
   and set it to `32400`. In Settings → Network, set **Secure connections**
   to **Preferred**.
6. On a phone with Wi-Fi disabled, open `app.plex.tv` and verify that `plex-k8`
   connects directly and securely, without a relay.

The UniFi and Plex settings are separate operational steps; changing the
Kubernetes manifests does not configure them or establish external connectivity.
