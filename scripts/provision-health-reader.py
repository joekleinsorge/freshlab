#!/usr/bin/env python3
"""Provision a narrow health credential; keep plaintext only in a protected output."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def run(args, data=None):
    return subprocess.check_output(args, input=data, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.is_symlink():
        raise SystemExit('Refusing to write a credential through a symlink')
    os.environ.setdefault('KUBECONFIG', str(ROOT / 'metal/kubeconfig.yaml'))
    os.environ.setdefault('SOPS_AGE_KEY_FILE', str(ROOT / 'key.txt'))
    run(['kubectl', 'apply', '-f', 'system/argo-workflows-ops/templates/host-health-reader.yaml'])
    name = 'freshlab-host-health-token'
    found = run(['kubectl', '-n', 'argocd', 'get', 'secret', name, '--ignore-not-found', '-o', 'json'])
    if not found:
        manifest = {'apiVersion': 'v1', 'kind': 'Secret', 'type': 'kubernetes.io/service-account-token',
                    'metadata': {'name': name, 'namespace': 'argocd', 'annotations': {'kubernetes.io/service-account.name': 'freshlab-host-health'}}}
        run(['kubectl', 'create', '-f', '-'], json.dumps(manifest).encode())
    for _ in range(30):
        secret = json.loads(run(['kubectl', '-n', 'argocd', 'get', 'secret', name, '-o', 'json']))
        if secret.get('data', {}).get('token'):
            break
        time.sleep(1)
    else:
        raise SystemExit('Controller did not populate the health token')
    # Store the controller-generated token encrypted, as required for all secrets.
    stored = {'apiVersion': 'v1', 'kind': 'Secret', 'type': secret['type'], 'data': secret['data'],
              'metadata': {'name': name, 'namespace': 'argocd', 'annotations': {'kubernetes.io/service-account.name': 'freshlab-host-health'}}}
    destination = Path('freshlab-secrets/host-health-token.sops.yaml')
    encrypted = run(['sops', '--encrypt', '--input-type', 'json', '--output-type', 'yaml',
                     '--filename-override', str(destination), '/dev/stdin'], json.dumps(stored).encode())
    (ROOT / destination).write_bytes(encrypted)
    generator = ROOT / 'freshlab-secrets/secret-generator.yaml'
    text = generator.read_text()
    if '  - host-health-token.sops.yaml\n' not in text:
        generator.write_text(text + '  - host-health-token.sops.yaml\n')
    cluster = json.loads(run(['kubectl', 'config', 'view', '--minify', '--raw', '-o', 'json']))['clusters'][0]['cluster']
    cluster = {k: v for k, v in cluster.items() if k in ('server', 'certificate-authority-data')}
    config = {'apiVersion': 'v1', 'kind': 'Config', 'current-context': 'health',
              'clusters': [{'name': 'freshlab', 'cluster': cluster}],
              'users': [{'name': 'health', 'user': {'token': base64.b64decode(secret['data']['token']).decode()}}],
              'contexts': [{'name': 'health', 'context': {'cluster': 'freshlab', 'user': 'health'}}]}
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(config, stream)
        stream.write('\n')
    for permission in (['get', 'secrets', '-A'], ['patch', 'volumes.longhorn.io', '-n', 'longhorn']):
        result = subprocess.run(['kubectl', '--kubeconfig', str(args.output), 'auth', 'can-i', *permission], capture_output=True, text=True)
        if result.stdout.strip() != 'no':
            raise SystemExit('Health credential unexpectedly has write or secret access')
    print(f'Read-only health kubeconfig written with mode 0600 to {args.output}; token stored only as SOPS ciphertext in Git.')


if __name__ == '__main__':
    main()
