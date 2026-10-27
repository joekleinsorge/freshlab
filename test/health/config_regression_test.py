import copy
import importlib.util
from pathlib import Path
import tempfile
import io
import tarfile
import unittest

path = Path(__file__).resolve().parents[2] / 'scripts/check-config-regressions.py'
spec = importlib.util.spec_from_file_location('config_regressions', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConfigRegressionTest(unittest.TestCase):
    def report(self):
        return {'SchemaVersion': 2, 'Results': [{'Target': 'app.yaml', 'Misconfigurations': [
            {'ID': 'KSV-0014', 'Message': 'Container app has a writable root',
             'Severity': 'HIGH', 'Status': 'FAIL'}]}]}

    def test_only_unchanged_sources_can_retain_existing_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            base, head = Path(directory) / 'base', Path(directory) / 'head'
            base.mkdir(); head.mkdir()
            (base / 'app.yaml').write_text('original workload')
            (head / 'app.yaml').write_text('original workload')
            report = self.report()
            added, retained = module.assess(report, report, base, head)
            self.assertFalse(added)
            self.assertEqual(sum(retained.values()), 1)
            (head / 'app.yaml').write_text('changed workload with the same security finding')
            added, _ = module.assess(report, report, base, head)
            self.assertEqual(sum(added.values()), 1)

    def test_duplicates_new_rules_and_new_resources_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'app.yaml').write_text('workload')
            before = self.report()
            for mutation in ('duplicate', 'rule', 'resource'):
                after = copy.deepcopy(before)
                problems = after['Results'][0]['Misconfigurations']
                if mutation == 'duplicate': problems.append(copy.deepcopy(problems[0]))
                if mutation == 'rule': problems[0]['ID'] = 'KSV-0017'
                if mutation == 'resource': problems[0]['Message'] = 'Container another has a writable root'
                with self.subTest(mutation=mutation):
                    added, _ = module.assess(before, after, root, root)
                    self.assertTrue(added)

    def test_missing_reports_and_outside_targets_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError): module.findings({}, root)
            report = self.report()
            report['Results'][0]['Target'] = '../outside.yaml'
            with self.assertRaises(ValueError): module.findings(report, root)

    def test_virtual_chart_templates_are_bound_to_the_vendored_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            charts = root / 'apps/example/charts'
            charts.mkdir(parents=True)
            def archive(content):
                with tarfile.open(charts / 'example-1.0.tgz', 'w:gz') as output:
                    member = tarfile.TarInfo('example/templates/deployment.yaml')
                    member.size = len(content)
                    output.addfile(member, io.BytesIO(content))
            archive(b'first workload')
            target = root / 'apps/example/charts/example/templates/deployment.yaml'
            first = module.source_digest(root, target)
            self.assertEqual(first, module.source_digest(root, target))
            archive(b'changed workload')
            self.assertNotEqual(first, module.source_digest(root, target))
