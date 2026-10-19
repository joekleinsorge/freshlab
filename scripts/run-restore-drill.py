#!/usr/bin/env python3
"""Start the declared disposable restore drill and require its verified outcome."""
import json
import os
from pathlib import Path
import subprocess
import time


def kubectl(*args, data=None):
    return subprocess.check_output(['kubectl', '--request-timeout=30s', '-n', 'argocd', *args], input=data)


def main():
    os.environ.setdefault('KUBECONFIG', str(Path(__file__).resolve().parents[1] / 'metal/kubeconfig.yaml'))
    cron = json.loads(kubectl('get', 'cronworkflow', 'freshlab-backup-restore-drill', '-o', 'json'))
    workflow = {'apiVersion': 'argoproj.io/v1alpha1', 'kind': 'Workflow',
                'metadata': {'generateName': 'freshlab-restore-drill-', 'namespace': 'argocd',
                             'labels': {'workflows.argoproj.io/cron-workflow': 'freshlab-backup-restore-drill'}},
                'spec': cron['spec']['workflowSpec']}
    created = json.loads(kubectl('create', '-f', '-', '-o', 'json', data=json.dumps(workflow).encode()))
    name = created['metadata']['name']
    print(f'Waiting for disposable restore and SQLite verification: {name}', flush=True)
    deadline = time.monotonic() + 5700
    while time.monotonic() < deadline:
        current = json.loads(kubectl('get', 'workflow', name, '-o', 'json'))
        phase = current.get('status', {}).get('phase')
        if phase in ('Succeeded', 'Failed', 'Error'):
            print(f'{name}: {phase}', flush=True)
            if phase != 'Succeeded': raise SystemExit(1)
            return
        time.sleep(15)
    raise SystemExit('Restore drill timed out; inspect its exit-handler cleanup before proceeding')


if __name__ == '__main__':
    main()
