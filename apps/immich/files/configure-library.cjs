const { createHash, randomBytes } = require('node:crypto');
const { constants, readFileSync } = require('node:fs');
const { access, opendir } = require('node:fs/promises');
const { createRequire } = require('node:module');
const { Client } = createRequire('/usr/src/app/server/package.json')('pg');

async function configure() {
  const desired = JSON.parse(readFileSync(`${__dirname}/library.json`, 'utf8'));
  // Use the same read-only NFS source as the server. The API's validation
  // endpoint requires unrestricted API access in v3.3.3; keep this key scoped.
  for (const path of desired.importPaths) {
    await access(path, constants.R_OK | constants.X_OK);
    const directory = await opendir(path);
    await directory.close();
  }
  const db = new Client({
    host: process.env.DB_HOSTNAME,
    user: 'immich',
    database: 'immich',
    password: process.env.DB_PASSWORD,
    connectionTimeoutMillis: 10000,
    query_timeout: 10000,
  });
  const keyName = 'freshlab-external-library-bootstrap';
  const token = randomBytes(32).toString('hex');
  let keyId;
  await db.connect();
  try {
    // Serialize retries and remove credentials left by an interrupted hook.
    const lock = await db.query("SELECT pg_try_advisory_lock(hashtext($1)) AS acquired", [keyName]);
    if (!lock.rows[0].acquired) throw new Error('Another library setup is running');
    const owner = await db.query(
      'SELECT id FROM "user" WHERE id = $1 AND "isAdmin" AND "deletedAt" IS NULL',
      [desired.ownerId],
    );
    if (owner.rowCount !== 1) throw new Error('Configured library owner must be an active administrator');
    await db.query('DELETE FROM api_key WHERE name = $1 AND "userId" = $2', [keyName, desired.ownerId]);
    // Bootstrap a short-lived, scoped credential; library mutations use Immich's API.
    const result = await db.query(
      'INSERT INTO api_key (name, key, "userId", permissions) VALUES ($1, $2, $3, $4) RETURNING id',
      [keyName, createHash('sha256').update(token).digest(), desired.ownerId,
        ['library.read', 'library.create', 'library.update']],
    );
    keyId = result.rows[0].id;

    async function api(path, method = 'GET', body) {
      const response = await fetch(`http://immich-server:2283/api/libraries${path}`, {
        method,
        headers: { 'x-api-key': token, 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(15000),
      });
      if (!response.ok) throw new Error(`Immich library API ${method} ${path}: HTTP ${response.status}`);
      return response.status === 204 ? undefined : response.json();
    }

    const libraries = await api('');
    const matches = libraries.filter((library) => library.name === desired.name
      || library.importPaths.some((path) => desired.importPaths.includes(path)));
    if (matches.length > 1) throw new Error('Multiple matching libraries; refusing to change import paths');
    let library = matches[0];
    if (library && library.ownerId !== desired.ownerId) throw new Error('Existing library belongs to another owner');
    if (!library) library = await api('', 'POST', desired);

    const settings = {
      name: desired.name,
      importPaths: desired.importPaths,
      exclusionPatterns: desired.exclusionPatterns,
    };
    if (Object.entries(settings).some(([key, value]) => JSON.stringify(library[key]) !== JSON.stringify(value))) {
      // Removing an existing path can mark its assets offline. Require manual review.
      if (library.importPaths.some((path) => !desired.importPaths.includes(path))) {
        throw new Error('Refusing to remove an existing library import path');
      }
      library = await api(`/${library.id}`, 'PUT', settings);
    }
    await api(`/${library.id}/scan`, 'POST');
    console.log(`${desired.name}: import path validated, library configured, scan queued (${library.id})`);
  } finally {
    try {
      if (keyId) await db.query('DELETE FROM api_key WHERE id = $1', [keyId]);
    } finally {
      await db.end();
    }
  }
}

configure().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
