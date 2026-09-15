# Media automation stack

Freshlab now includes the optional Plex automation services under `apps/`:
Prowlarr, FlareSolverr, Sonarr, Radarr, Bazarr, qBittorrent, Seerr,
Tautulli, Autobrr, and Recyclarr.

The *arr workloads and qBittorrent share `192.168.1.208:/volume1/Media` (as
`/data` and `/downloads`, respectively). Adjust that export or the mount paths
before syncing if the media layout differs, and configure the *arr
download/import paths accordingly.

Before enabling qBittorrent, create its PIA OpenVPN credentials in the
`qbittorrent` namespace. The namespace is intentionally marked privileged
because Gluetun needs `NET_ADMIN` and `/dev/net/tun`:

```sh
kubectl -n qbittorrent create secret generic qbittorrent-secrets \
  --from-literal=PIA_OPENVPN_USERNAME='replace-me' \
  --from-literal=PIA_OPENVPN_PASSWORD='replace-me'
```

Gluetun uses PIA's native OpenVPN integration here; PIA WireGuard requires a
custom generated configuration and is not used by this manifest. Replace the
placeholders with a SOPS-managed Secret before committing a production
configuration. Configure the *arr API keys in a Secret named
`recyclarr-secrets` with `SONARR_API_KEY` and `RADARR_API_KEY`.

After the pods are healthy, configure the applications using these internal
service addresses:

- Sonarr: `http://sonarr.sonarr.svc.cluster.local:8989`
- Radarr: `http://radarr.radarr.svc.cluster.local:7878`
- Prowlarr: `http://prowlarr.prowlarr.svc.cluster.local:9696`
- qBittorrent: `http://qbittorrent.qbittorrent.svc.cluster.local:8080`
- Plex: `http://plex.plex.svc.cluster.local:32400`
