import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'plex_update', Path(__file__).resolve().parents[2] / 'scripts/synology-plex-update.py'
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)
PUBLIC = '1.43.5.11029-6bf8af3f0'
DIGEST = updater.IMAGE + '@sha256:' + 'a' * 64


def feed():
    return io.BytesIO(json.dumps({'computer': {'Linux': {'version': PUBLIC}}}).encode())


class PlexUpdateTest(unittest.TestCase):
    def test_current_server_does_not_pull_or_restart(self):
        with patch('sys.argv', ['update', '--apply']), \
                patch.object(updater.urllib.request, 'urlopen', return_value=feed()), \
                patch.object(updater, 'version', return_value=PUBLIC), \
                patch.object(updater, 'run') as run:
            updater.main()
            run.assert_not_called()

    def test_image_must_match_public_release_before_deployment(self):
        image = {'Config': {'Labels': {'org.opencontainers.image.version': '1.43.4-old-ls327'}}}
        with tempfile.TemporaryDirectory() as directory, \
                patch('sys.argv', ['update', '--apply']), \
                patch.object(updater.urllib.request, 'urlopen', return_value=feed()), \
                patch.object(updater, 'version', return_value='1.43.4.10903-old'), \
                patch.object(updater.os, 'geteuid', return_value=0), \
                patch.object(updater, 'STATE', Path(directory)), \
                patch.object(updater, 'run', side_effect=['', json.dumps([image])]) as run:
            with self.assertRaisesRegex(SystemExit, 'does not match'):
                updater.main()
            self.assertEqual(run.call_count, 2)
            self.assertFalse((Path(directory) / 'compose-image.json').exists())

    def test_update_pins_digest_and_only_recreates_plex(self):
        image = {'Config': {'Labels': {'org.opencontainers.image.version': PUBLIC + '-ls329'}},
                 'RepoDigests': [DIGEST]}
        response = io.BytesIO(b'healthy')
        response.status = 200
        with tempfile.TemporaryDirectory() as directory, \
                patch('sys.argv', ['update', '--apply']), \
                patch.object(updater.urllib.request, 'urlopen', side_effect=[feed(), response]), \
                patch.object(updater, 'version', side_effect=['1.43.4.10903-old', PUBLIC]), \
                patch.object(updater.os, 'geteuid', return_value=0), \
                patch.object(updater.os, 'chdir'), \
                patch.object(updater, 'STATE', Path(directory)), \
                patch.object(updater, 'run', side_effect=['', json.dumps([image]), '']) as run:
            updater.main()
            override = json.loads((Path(directory) / 'compose-image.json').read_text())
            self.assertEqual(override, {'version': '3.9', 'services': {'plex': {'image': DIGEST}}})
            self.assertEqual(run.call_args.args[-4:], ('up', '-d', '--no-deps', 'plex'))


if __name__ == '__main__':
    unittest.main()
