#!/usr/bin/env python3
"""Necessary aggregate capacity check, not a proof of scheduler/affinity fit."""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess


def quantity(value):
    value = str(value)
    units = {'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, 'Ti': 1024**4,
             'n': Decimal('0.000000001'), 'u': Decimal('0.000001'), 'm': Decimal('0.001'),
             'k': 1000, 'K': 1000, 'M': 1000**2, 'G': 1000**3, 'T': 1000**4}
    for suffix, multiplier in units.items():
        if value.endswith(suffix): return Decimal(value[:-len(suffix)]) * multiplier
    return Decimal(value)


def requests(pod):
    result = {}
    for resource in ('cpu', 'memory'):
        regular = sum(quantity(c.get('resources', {}).get('requests', {}).get(resource, 0)) for c in pod['spec'].get('containers', []))
        # Restartable init containers remain running beside app containers.
        sidecars, initializing = Decimal(0), Decimal(0)
        for container in pod['spec'].get('initContainers', []):
            request = quantity(container.get('resources', {}).get('requests', {}).get(resource, 0))
            if container.get('restartPolicy') == 'Always': sidecars += request
            initializing = max(initializing, sidecars + (0 if container.get('restartPolicy') == 'Always' else request))
        result[resource] = max(regular + sidecars, initializing, quantity(pod['spec'].get('resources', {}).get('requests', {}).get(resource, 0)))
        result[resource] += quantity(pod['spec'].get('overhead', {}).get(resource, 0))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exclude-node')
    parser.add_argument('--headroom-percent', type=int, default=20)
    args = parser.parse_args()
    if not 0 <= args.headroom_percent < 100: raise SystemExit('Headroom must be between 0 and 99')
    os.environ.setdefault('KUBECONFIG', str(Path(__file__).resolve().parents[1] / 'metal/kubeconfig.yaml'))
    nodes = json.loads(subprocess.check_output(['kubectl', '--request-timeout=15s', 'get', 'nodes', '-o', 'json']))['items']
    pods = json.loads(subprocess.check_output(['kubectl', '--request-timeout=15s', 'get', 'pods', '-A', '-o', 'json']))['items']
    failures = 0
    for target in ([args.exclude_node] if args.exclude_node else [n['metadata']['name'] for n in nodes]):
        if target not in {n['metadata']['name'] for n in nodes}: raise SystemExit('Unknown target node')
        survivors = [n for n in nodes if n['metadata']['name'] != target and any(c['type'] == 'Ready' and c['status'] == 'True' for c in n['status']['conditions'])]
        needed = {'cpu': Decimal(0), 'memory': Decimal(0)}
        for pod in pods:
            if pod.get('status', {}).get('phase') in ('Succeeded', 'Failed'): continue
            local = pod['spec'].get('nodeName') == target
            per_node = any(o['kind'] in ('DaemonSet', 'Node') for o in pod['metadata'].get('ownerReferences', []))
            if local and per_node: continue
            for resource, value in requests(pod).items(): needed[resource] += value
        capacity = {r: sum(quantity(n['status']['allocatable'].get(r, 0)) for n in survivors) for r in needed}
        limit = {r: total * (100 - args.headroom_percent) / 100 for r, total in capacity.items()}
        fits = all(needed[r] <= limit[r] for r in needed)
        print(f"Without {target}: CPU requests {needed['cpu']:.2f}/{limit['cpu']:.2f} cores; memory requests {needed['memory']/1024**3:.1f}/{limit['memory']/1024**3:.1f} GiB ({args.headroom_percent}% headroom): {'PASS' if fits else 'FAIL'}")
        failures += not fits
    print('This checks aggregate requests only. Affinity, GPUs, storage placement, actual usage, and network paths still require a controlled drill.')
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__': main()
