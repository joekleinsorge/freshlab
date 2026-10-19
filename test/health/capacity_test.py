import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / 'scripts/check-failure-capacity.py'
spec = importlib.util.spec_from_file_location('capacity', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CapacityTest(unittest.TestCase):
    def test_kubernetes_units(self):
        self.assertEqual(module.quantity('1500m'), module.quantity('1.5'))
        self.assertEqual(module.quantity('1Gi'), module.quantity('1024Mi'))

    def test_init_peak_is_not_added_to_steady_app_requests(self):
        pod = {'spec': {'containers': [{'resources': {'requests': {'memory': '1Gi'}}}],
                        'initContainers': [{'resources': {'requests': {'memory': '2Gi'}}}]}}
        self.assertEqual(module.requests(pod)['memory'], module.quantity('2Gi'))

    def test_restartable_init_remains_beside_apps(self):
        pod = {'spec': {'containers': [{'resources': {'requests': {'memory': '1Gi'}}}],
                        'initContainers': [{'restartPolicy': 'Always', 'resources': {'requests': {'memory': '512Mi'}}},
                                           {'resources': {'requests': {'memory': '2Gi'}}}],
                        'overhead': {'memory': '128Mi'}}}
        self.assertEqual(module.requests(pod)['memory'], module.quantity('2688Mi'))
