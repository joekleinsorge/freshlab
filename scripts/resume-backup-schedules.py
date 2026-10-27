#!/usr/bin/env python3
"""Restore scheduled backups after completed one-shot VolSync triggers."""
import argparse
import json
import subprocess


def resume_patch(source):
    spec = source.get('spec', {})
    trigger = spec.get('trigger', {})
    status = source.get('status', {})
    manual = trigger.get('manual')
    running = any(c.get('type') == 'Synchronizing' and c.get('status') == 'True'
                  for c in status.get('conditions', []))
    if (spec.get('paused') or not trigger.get('schedule') or not manual or running
            or status.get('lastManualSync') != manual):
        return None
    # Do not erase a newer operator trigger or race a controller update.
    return [
        {'op': 'test', 'path': '/metadata/resourceVersion', 'value': source['metadata']['resourceVersion']},
        {'op': 'test', 'path': '/spec/trigger/manual', 'value': manual},
        {'op': 'remove', 'path': '/spec/trigger/manual'},
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='apply repairs; otherwise only report')
    parser.add_argument('--limit', type=int, default=2, help='maximum sources to resume in one batch')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    result = subprocess.run(['kubectl', '--request-timeout=15s', 'get', 'replicationsource',
                             '-A', '-o', 'json'], capture_output=True, text=True, check=True)
    sources = sorted(json.loads(result.stdout)['items'],
                     key=lambda s: (s['metadata']['namespace'], s['metadata']['name']))
    resumed = 0
    for source in sources:
        patch = resume_patch(source)
        if patch is None:
            continue
        meta = source['metadata']
        label = f"{meta['namespace']}/{meta['name']}"
        if not args.apply:
            print(f'Ready to resume: {label}')
            continue
        if resumed >= args.limit:
            print(f'Deferred to next batch: {label}')
            continue
        subprocess.run(['kubectl', '--request-timeout=15s', '-n', meta['namespace'], 'patch',
                        'replicationsource', meta['name'], '--type=json', '-p', json.dumps(patch)], check=True)
        resumed += 1
    if args.apply:
        print(f'Resumed {resumed} scheduled backup(s). Wait for this batch before resuming more.')


if __name__ == '__main__':
    main()
