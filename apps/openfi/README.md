# OpenFI on Freshlab

This chart is deployed by Freshlab's root Argo CD ApplicationSet from `apps/openfi`.
It uses a retained Longhorn claim and a single Recreate deployment for SQLite.
The chart, image digest, route, and backup policy contain no household records
or login credentials.

The private SQLite database is installed on the PVC. A unique Restic repository
secret is provisioned in the `openfi` namespace outside Git; its repository
encryption key is retained in the ignored `data/private/openfi-restic.json` file.
VolSync snapshots the PVC on the configured schedule. Keep the source household
file and login credentials in the ignored private data directory as well.

Public access is authenticated by OAuth2 Proxy against Dex. The Dex `openfi-users`
group is allow-listed, and the trusted Dex email is mapped to the existing
owner account without changing the SQLite household. OIDC client/cookie secrets,
the Dex password hash, and the email mapping are provisioned as runtime Secrets
outside Git. The planner listens on pod loopback and is reachable externally
only through the authenticated proxy.

Before upgrades, create an online backup with `scripts/backup.py`. To recover,
restore the PVC to a separate claim and verify SQLite integrity before
repointing the deployment.

## Private source import

`scripts/import_household.py` takes a supplied household JSON document and
creates a new, owner-only database, generated login, and importable plan JSON:

```sh
python3 scripts/import_household.py data/private/household-source.json \
  --database data/private/planner.sqlite3 \
  --credentials data/private/login.json
```

It refuses existing database/credential paths. Use it offline, not against a
running server. The full source is preserved in the plan and shown in Settings.
The importer distinguishes original facts from draft modeling assumptions;
reference-only debts retain their balances without adding duplicate cash
payments. Child birth dates, beneficiary mappings, and unknown mortgage terms
are not invented. Disabled purchases retain costs without inventing timing.
Base, conservative, and adverse scenarios are labeled illustrative drafts.

The `data/` directory is excluded from Git and the Docker build context. The
Dockerfile only copies application code and web assets. Do not embed a private
source document as a test fixture or static web resource.
