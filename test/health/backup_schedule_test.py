import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / 'scripts/resume-backup-schedules.py'
spec = importlib.util.spec_from_file_location('backup_schedule', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BackupScheduleTest(unittest.TestCase):
    def source(self):
        return {'metadata': {'resourceVersion': '123'},
                'spec': {'trigger': {'schedule': '0 */6 * * *', 'manual': 'once'}},
                'status': {'lastManualSync': 'once', 'conditions': [
                    {'type': 'Synchronizing', 'status': 'False'}]}}

    def test_completed_override_is_removed_with_concurrency_guards(self):
        patch = module.resume_patch(self.source())
        self.assertEqual(patch[0], {'op': 'test', 'path': '/metadata/resourceVersion', 'value': '123'})
        self.assertEqual(patch[1], {'op': 'test', 'path': '/spec/trigger/manual', 'value': 'once'})
        self.assertEqual(patch[-1], {'op': 'remove', 'path': '/spec/trigger/manual'})

    def test_active_paused_and_unscheduled_sources_are_preserved(self):
        for case in ('running', 'paused', 'not_completed', 'no_schedule'):
            s = self.source()
            if case == 'running': s['status']['conditions'][0]['status'] = 'True'
            if case == 'paused': s['spec']['paused'] = True
            if case == 'not_completed': s['status']['lastManualSync'] = 'previous'
            if case == 'no_schedule': del s['spec']['trigger']['schedule']
            with self.subTest(case=case): self.assertIsNone(module.resume_patch(s))
