import copy
import datetime as dt
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / 'scripts/check-cluster-state.py'
spec = importlib.util.spec_from_file_location('cluster_state', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 10, 19, 18, tzinfo=dt.timezone.utc)
        self.policy = {'expected_nodes': ['metal1'], 'volumes': [
            {'namespace': 'app', 'pvc': 'data', 'backup_source': 'data', 'min_replicas': 2, 'max_backup_age_hours': 8}]}
        self.state = {
            'nodes': [{'metadata': {'name': 'metal1'}, 'status': {'conditions': [
                {'type': t, 'status': 'True' if t == 'Ready' else 'False'}
                for t in ['Ready', 'DiskPressure', 'MemoryPressure', 'PIDPressure']]}}],
            'pvc': [{'metadata': {'namespace': 'app', 'name': 'data'}, 'spec': {'volumeName': 'v'}, 'status': {'phase': 'Bound'}}],
            'volumes.longhorn.io': [{'metadata': {'name': 'v'}, 'spec': {'numberOfReplicas': 2}}],
            'replicas.longhorn.io': [{'spec': {'volumeName': 'v', 'nodeID': n, 'healthyAt': '2026-10-19T01:00:00Z'}} for n in ['metal1', 'metal2']],
            'replicationsources.volsync.backube': [{'metadata': {'namespace': 'app', 'name': 'data'}, 'spec': {'sourcePVC': 'data'},
                'status': {'lastSyncTime': '2026-10-19T13:00:00Z', 'latestMoverStatus': {'result': 'Successful'}}}],
            'snapshots.longhorn.io': [], 'engines.longhorn.io': []}

    def assess(self):
        return module.assess(self.state, self.policy, self.now)

    def test_healthy(self):
        self.assertEqual(self.assess(), [])

    def test_ready_node_with_disk_pressure_fails(self):
        self.state['nodes'][0]['status']['conditions'][1]['status'] = 'True'
        self.assertTrue(any('DiskPressure' in f for f in self.assess()))

    def test_one_healthy_copy_is_not_redundancy(self):
        self.state['replicas.longhorn.io'].pop()
        self.assertTrue(any('independent healthy' in f for f in self.assess()))

    def test_two_copies_on_same_node_fail(self):
        self.state['replicas.longhorn.io'][1]['spec']['nodeID'] = 'metal1'
        self.assertTrue(self.assess())

    def test_failed_replica_does_not_count(self):
        self.state['replicas.longhorn.io'][1]['spec']['failedAt'] = '2026-10-19T17:00:00Z'
        self.assertTrue(self.assess())

    def test_stale_missing_paused_and_wrong_source_backups_fail(self):
        healthy = copy.deepcopy(self.state)
        for mutation in ['stale', 'missing', 'paused', 'wrong']:
            self.state = copy.deepcopy(healthy)
            sources = self.state['replicationsources.volsync.backube']
            if mutation == 'stale': sources[0]['status']['lastSyncTime'] = '2026-10-18T00:00:00Z'
            if mutation == 'missing': sources.clear()
            if mutation == 'paused': sources[0]['spec']['paused'] = True
            if mutation == 'wrong': sources[0]['spec']['sourcePVC'] = 'retired-data'
            with self.subTest(mutation=mutation): self.assertTrue(self.assess())

    def test_snapshot_purge_error_is_reported(self):
        self.state['snapshots.longhorn.io'] = [{'metadata': {'name': 'stuck'}, 'status': {'error': 'engine upgrade incomplete'}}]
        self.assertTrue(any('upgrade incomplete' in f for f in self.assess()))


if __name__ == '__main__':
    unittest.main()
