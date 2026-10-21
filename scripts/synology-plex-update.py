#!/usr/bin/env python3
"""Update only Synology Plex to the public release, using a resolved image digest."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET


DOCKER = '/var/packages/Docker/target/usr/bin/docker'
COMPOSE = '/var/packages/Docker/target/usr/bin/docker-compose'
PROJECT = Path('/volume1/docker/git')
STATE = Path('/var/lib/freshlab-plex')
IMAGE = 'lscr.io/linuxserver/plex'


def run(*args):
    return subprocess.check_output(args, text=True, timeout=600).strip()


def version():
    with urllib.request.urlopen('http://127.0.0.1:32400/identity', timeout=15) as response:
        return ET.fromstring(response.read()).attrib['version']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Pull and deploy when outdated')
    args = parser.parse_args()
    with urllib.request.urlopen('https://plex.tv/api/downloads/5.json', timeout=30) as response:
        public = json.load(response)['computer']['Linux']['version']
    current = version()
    print('Installed: {}; latest public: {}'.format(current, public), flush=True)
    if current == public:
        return
    # Do not downgrade a newer release or a deliberately installed beta.
    numbers = lambda value: tuple(int(n) for n in value.split('-')[0].split('.'))
    if numbers(current) >= numbers(public):
        raise SystemExit('Installed version is ahead of public; manual review required')
    if not args.apply:
        raise SystemExit('Plex is outdated; run with --apply as root to update')
    if os.geteuid() != 0:
        raise SystemExit('--apply requires root')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (STATE / 'update.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Resolve stable latest once, then deploy the immutable digest. Refuse
        # an image that has not yet caught up with Plex's public release feed.
        run(DOCKER, 'pull', IMAGE + ':latest')
        image = json.loads(run(DOCKER, 'image', 'inspect', IMAGE + ':latest'))[0]
        label = image['Config']['Labels']['org.opencontainers.image.version']
        if not label.startswith(public + '-ls'):
            raise SystemExit('Container release does not match public Plex release: ' + label)
        digest = next(item for item in image['RepoDigests'] if item.startswith(IMAGE + '@sha256:'))
        override = STATE / 'compose-image.json'
        pending = STATE / 'compose-image.json.tmp'
        pending.write_text(json.dumps({'version': '3.9', 'services': {'plex': {'image': digest}}}) + '\n')
        pending.replace(override)
        os.chdir(str(PROJECT))
        run(COMPOSE, '-f', str(PROJECT / 'docker-compose.yml'), '-f', str(override),
            'up', '-d', '--no-deps', 'plex')
        for attempt in range(60):
            try:
                if version() == public:
                    with urllib.request.urlopen('http://127.0.0.1:32400/web/', timeout=10) as response:
                        if response.status == 200:
                            print('Updated and healthy: ' + public)
                            return
            except (OSError, ET.ParseError):
                pass
            time.sleep(5)
        raise SystemExit('Update did not become healthy within five minutes; inspect Plex before retrying')


if __name__ == '__main__':
    main()
