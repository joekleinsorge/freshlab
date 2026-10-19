#!/usr/bin/env python3
"""Initialize declared backups serially during recovery, then record activation."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def kubectl(*args, data=None):
    return subprocess.check_output(['kubectl', '--request-timeout=30s', *args], input=data, cwd=ROOT)


def active_in_git(source):
    path = ROOT / 'system/volsync-system/values.yaml'
    blocks = re.split(r'(?=^    - namespace:)', path.read_text(), flags=re.M)
    for i, block in enumerate(blocks):
        if re.search(r'^      pvc: ' + re.escape(source) + r'\s*$', block, flags=re.M):
            blocks[i] = re.sub(r'^      paused: true$', '      paused: false', block, flags=re.M)
    path.write_text(''.join(blocks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--include-bulk', action='store_true')
    parser.add_argument('--repair-pod-images', action='store_true', help='Emergency only: repair never-started movers using the known missing digest')
    parser.add_argument('--timeout-seconds', type=int, default=1800)
    args = parser.parse_args()
    os.environ.setdefault('KUBECONFIG', str(ROOT / 'metal/kubeconfig.yaml'))
    policy = json.loads((ROOT / 'docs/operations/reliability-policy.json').read_text())
    if args.apply:
        app = json.loads(kubectl('-n', 'argocd', 'get', 'application', 'volsync-system', '-o', 'json'))
        preserved = any(r.get('group') == 'volsync.backube' and r.get('kind') == 'ReplicationSource'
                        and '/spec/trigger/manual' in r.get('jsonPointers', [])
                        for r in app['spec'].get('ignoreDifferences', []))
        if not preserved and not args.repair_pod_images:
            raise SystemExit('Sync the declared manual-backup trigger preservation before initializing backups')
        controller = json.loads(kubectl('-n', 'volsync-system', 'get', 'deployment', 'volsync-system', '-o', 'json'))
        expected = 'sha256:0d03a6aad57569eba2c0eaa0848cf4a908d9744b372ff2224bb291a320f36d76'
        if not controller['spec']['template']['spec']['containers'][0]['image'].endswith(expected) and not args.repair_pod_images:
            raise SystemExit('Sync the verified VolSync controller image before initializing backups')
    rendered = subprocess.check_output(['helm', 'template', 'volsync-system', 'system/volsync-system', '-n', 'volsync-system'], cwd=ROOT)
    documents = json.loads(subprocess.check_output(['ruby', '-ryaml', '-rjson', '-e',
        'puts JSON.generate(YAML.load_stream(STDIN.read).compact.select { |v| v["kind"] == "ReplicationSource" })'], input=rendered))
    manifests = {(d['metadata']['namespace'], d['metadata']['name']): d for d in documents}
    for item in policy['volumes']:
        namespace, source = item['namespace'], item['backup_source']
        if item['max_backup_age_hours'] > 8 and not args.include_bulk: continue
        raw = kubectl('-n', namespace, 'get', 'replicationsource', source, '--ignore-not-found', '-o', 'json')
        current = json.loads(raw) if raw else None
        if current:
            last = current.get('status', {}).get('lastSyncTime')
            age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last.replace('Z', '+00:00'))).total_seconds() if last else float('inf')
            if 0 <= age < item['max_backup_age_hours'] * 3600 and not current['spec'].get('paused', False) and current['spec']['sourcePVC'] == item['pvc'] and current.get('status', {}).get('latestMoverStatus', {}).get('result') == 'Successful':
                if args.apply: active_in_git(source)
                print(f'Already current: {namespace}/{source}', flush=True)
                continue
        print(f'Initialize backup: {namespace}/{source}', flush=True)
        if not args.apply: continue
        if args.repair_pod_images and current and current['metadata'].get('annotations', {}).get('argocd.argoproj.io/tracking-id'):
            raise SystemExit('Publish/sync the image fix before restarting an Argo-managed existing source')
        if current and current['metadata'].get('annotations', {}).get('argocd.argoproj.io/tracking-id') and current['spec'].get('paused'):
            raise SystemExit('Activate this source in Git and sync it before requesting a backup')
        for node in json.loads(kubectl('get', 'nodes', '-o', 'json'))['items']:
            conditions = {c['type']: c['status'] for c in node['status']['conditions']}
            if conditions.get('Ready') != 'True' or any(conditions.get(p) != 'False' for p in ('DiskPressure', 'MemoryPressure', 'PIDPressure')):
                raise SystemExit('Stop admitting backups until node readiness and pressure recover')
        manifest = manifests.get((namespace, source))
        if not manifest:
            if not current: raise SystemExit('No declared source manifest found')
            manifest = {k: current[k] for k in ('apiVersion', 'kind', 'spec')}
            manifest['metadata'] = {'name': source, 'namespace': namespace}
        previous = current.get('spec', {}).get('trigger', {}).get('manual', '') if current else ''
        unfinished = current and current.get('status', {}).get('lastManualSync') != previous
        request = previous if unfinished and previous.startswith('reliability-') else 'reliability-' + uuid.uuid4().hex[:16]
        manifest['spec']['paused'] = False
        manifest['spec']['trigger']['manual'] = request
        kubectl('apply', '-f', '-', data=json.dumps(manifest).encode())
        deadline = time.monotonic() + args.timeout_seconds
        while time.monotonic() < deadline:
            if args.repair_pod_images:
                pods = json.loads(kubectl('-n', namespace, 'get', 'pods', '-l', 'job-name=volsync-src-' + source, '-o', 'json'))['items']
                missing = 'quay.io/backube/volsync@sha256:758330413ac6ef0642dae4748dcad6c94146869d783b7cffd021f4808b8f77ac'
                image = 'quay.io/backube/volsync@sha256:0d03a6aad57569eba2c0eaa0848cf4a908d9744b372ff2224bb291a320f36d76'
                for pod in pods:
                    statuses = {s['name']: s for s in pod.get('status', {}).get('containerStatuses', [])}
                    for index, container in enumerate(pod['spec']['containers']):
                        state = statuses.get(container['name'], {})
                        never_started = not state.get('restartCount') and not state.get('lastState')
                        waiting = state.get('state', {}).get('waiting', {}).get('reason') in ('ErrImagePull', 'ImagePullBackOff')
                        if container['name'] == 'restic' and container['image'] == missing and never_started and waiting:
                            patch = [{'op': 'replace', 'path': f'/spec/containers/{index}/image', 'value': image}]
                            kubectl('-n', namespace, 'patch', 'pod', pod['metadata']['name'], '--type=json', '-p', json.dumps(patch))
                            print(f'Repaired missing image for never-started mover: {namespace}/{source}', flush=True)
            current = json.loads(kubectl('-n', namespace, 'get', 'replicationsource', source, '-o', 'json'))
            status = current.get('status', {})
            if status.get('lastManualSync') == request:
                if status.get('latestMoverStatus', {}).get('result') != 'Successful':
                    raise SystemExit(f'{namespace}/{source}: backup did not succeed')
                active_in_git(source)
                print(f'Backup verified and activation recorded: {namespace}/{source}', flush=True)
                break
            time.sleep(10)
        else:
            kubectl('-n', namespace, 'patch', 'replicationsource', source, '--type=merge', '-p', '{"spec":{"paused":true}}')
            raise SystemExit(f'{namespace}/{source}: backup timed out; source paused for investigation')


if __name__ == '__main__':
    main()
