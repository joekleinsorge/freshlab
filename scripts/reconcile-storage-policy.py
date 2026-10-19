#!/usr/bin/env python3
"""Increase required replica counts after a capacity check; never delete data."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def get(resource, namespace=None, name=None):
    command = ['kubectl', '--request-timeout=15s']
    if namespace: command += ['-n', namespace]
    command += ['get', resource]
    if name: command += [name]
    command += ['-o', 'json']
    return json.loads(subprocess.check_output(command))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    os.environ.setdefault('KUBECONFIG', str(ROOT / 'metal/kubeconfig.yaml'))
    policy = json.loads((ROOT / 'docs/operations/reliability-policy.json').read_text())
    if args.apply:
        for node in get('nodes')['items']:
            conditions = {c['type']: c['status'] for c in node['status']['conditions']}
            if conditions.get('Ready') != 'True' or any(conditions.get(p) != 'False' for p in ['DiskPressure', 'MemoryPressure', 'PIDPressure']):
                raise SystemExit('Resolve node readiness/pressure before increasing replication')
    for item in policy['volumes']:
        claim = get('pvc', item['namespace'], item['pvc'])
        name = claim['spec']['volumeName']
        volume = get('volumes.longhorn.io', 'longhorn', name)
        minimum = item['min_replicas']
        if volume['spec']['numberOfReplicas'] >= minimum: continue
        print(f"{item['namespace']}/{item['pvc']}: increase replicas to {minimum}", flush=True)
        if not args.apply: continue
        if volume['status']['robustness'] != 'healthy':
            raise SystemExit('Existing source volume must be healthy before changing replica count')
        # Require room for a full replica and the declared scheduling floor
        # on independent nodes, including copies already present. This is
        # conservative; Longhorn still makes the final scheduling decision.
        required = max(int(volume['spec']['size']), int(volume['status'].get('actualSize', 0)))
        existing = get('replicas.longhorn.io', 'longhorn')['items']
        eligible_nodes = {r['spec'].get('nodeID') for r in existing
                          if r['spec'].get('volumeName') == name and r['spec'].get('healthyAt')
                          and not r['spec'].get('failedAt') and r['spec'].get('nodeID')}
        for node in get('nodes.longhorn.io', 'longhorn')['items']:
            if not node['spec'].get('allowScheduling'): continue
            if any(d.get('storageAvailable', 0) >= required + d.get('storageMaximum', 0) * policy['min_node_free_fraction']
                   and all(c['status'] == 'True' for c in d.get('conditions', []) if c['type'] in ('Ready', 'Schedulable'))
                   for d in node['status'].get('diskStatus', {}).values()):
                eligible_nodes.add(node['metadata']['name'])
        if len(eligible_nodes) < minimum:
            raise SystemExit('Insufficient independent disk headroom; no storage policy was weakened')
        subprocess.check_call(['kubectl', '-n', 'longhorn', 'patch', 'volumes.longhorn.io', name,
                               '--type=merge', '-p', json.dumps({'spec': {'numberOfReplicas': minimum}})])
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            refreshed = get('volumes.longhorn.io', 'longhorn', name)
            replicas = get('replicas.longhorn.io', 'longhorn')['items']
            healthy_nodes = {r['spec'].get('nodeID') for r in replicas
                             if r['spec'].get('volumeName') == name and r['spec'].get('healthyAt')
                             and not r['spec'].get('failedAt') and r['spec'].get('nodeID')}
            if refreshed['status']['robustness'] == 'healthy' and len(healthy_nodes) >= minimum: break
            time.sleep(10)
        else:
            raise SystemExit('Replica rebuild did not become healthy within 20 minutes; stop and investigate')


if __name__ == '__main__':
    main()
