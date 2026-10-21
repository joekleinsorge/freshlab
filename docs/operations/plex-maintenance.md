# Plex maintenance

## Updates without an agent

Kubernetes Plex uses the existing Renovate and Argo CD services. The Plex-only
rule in `renovate.json` separates its digest updates from other applications,
allows them at any time, and lets Renovate merge after required checks pass.
`platformAutomerge: false` lets Renovate perform the merge without enabling
GitHub's repository-wide automatic merge feature. Both the StatefulSet and GPU
smoke test retain the same immutable image digest. Argo CD reconciles `main`.
This runs on Renovate's service cadence; it is not an instantaneous update
guarantee. A failed check blocks merging and must be investigated.

Synology Plex is a Docker container, not a DSM Plex package. Its current Compose
project is `/volume1/docker/git/docker-compose.yml`, with configuration under
`/volume1/docker/plex2`. Do not use DSM Package Center to update it.

`scripts/synology-plex-update.py` checks Plex's official public release feed.
Without `--apply` it only checks the installed version. With `--apply`, it pulls
the LinuxServer stable image, verifies that its version matches the public Plex
release, resolves its immutable digest, and updates only the `plex` service.
It waits for the API and web interface to respond successfully. A concurrent
run, download failure, version mismatch, or failed health check returns an error.
It does not automatically downgrade or delete configuration, media, or images.
Keep the existing backup/snapshot policy; rollback can require restoring the
configuration if Plex has migrated its database.

Install once on Synology by running the reviewed installer with sudo. Both
scripts must be in the same directory:

```sh
sudo sh /var/services/homes/Kleinsorge/freshlab-plex-maintenance/install-synology-plex-update.sh
```

The installer places root-owned executables under `/usr/local/sbin` and a daily
05:00 NAS-local cron entry in `/etc/cron.d/freshlab-plex-update`. The installed
DSM cron daemon supports `/etc/cron.d`. It runs the updater immediately once;
subsequent runs require no login or Codex. Failure sends a DSM notification to
`@administrators`; enable the desired notification delivery in DSM. Only the
most recent run's output is retained at `/var/lib/freshlab-plex/last-run.log`.
Verify the root-owned cron entry and first run after installation, and verify
the custom cron file survives future DSM upgrades. To disable updates, remove
only `/etc/cron.d/freshlab-plex-update`.

The root-only `/var/lib/freshlab-plex/compose-image.json` is generated update
state, not a second hand-maintained Compose project. Future manual Compose
commands must include this override to retain the resolved digest; a base-only
`up` uses the original image setting. Do not store credentials in this script.
The script and task need installation once; neither needs Codex to run.

## Security check on 2026-10-21

Both live APIs reported `1.43.5.11029-6bf8af3f0`, above the fixed version
`1.43.3.10861` in [Plex's security notice](https://forums.plex.tv/t/important-security-update-for-plex-media-server-v1-43-2-and-earlier/942319/).

Read-only investigation found no published malware-name or exploit-pattern
matches in 103 retained Kubernetes Plex logs or 68 retained Synology Plex logs.
Neither Preferences.xml contained unexpected transcoder options. Shared codec
libraries had identical SHA-256 hashes between the installations; this is a
cross-check, not verification against a vendor-signed clean baseline.

On metal1, Plex executables resolved inside the expected image paths. Process,
temporary-directory, cron, and service checks found no published malware-name
indicators or executables running from temporary directories. Retained SSH
authentication events checked since October 16 used the existing LAN client
and key. The journal retained history only from October 9 onward.

Synology's readable process command lines and accessible startup/temporary files
were inspected for published malware-name indicators. Root-only executable
links, authentication logs, scheduled tasks, and persistence locations could
not be fully inspected without sudo. Its main Plex server logs rotated back
only to October 20; older component logs do not replace missing access logs.

No positive indicator was identified in the inspected evidence. These checks
cannot establish that either host has never been compromised. In particular,
the Synology host-level investigation remains incomplete until administrative
access is available. Preserve evidence and follow Plex's recovery guidance if
any indicator appears; do not erase codec directories as a substitute for
investigation.
