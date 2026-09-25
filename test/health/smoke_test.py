"""Exercise failure aggregation, protected app availability and route selection."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/cluster-smoke-test"

class SmokeTest(unittest.TestCase):
    def run_check(self, failing=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kubectl = root / "kubectl"
            kubectl.write_text("""#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if args[0] == 'wait': sys.exit(0)
if 'applications.argoproj.io' in args:
 data = [{'metadata': {'name':'app'}, 'status': {'health': {'status':'Progressing' if os.getenv('FAIL_CASE') else 'Healthy'}, 'sync': {'status':'Synced'}}}]
elif 'deployments,statefulsets,daemonsets' in args:
 data = [{'kind':'Deployment','metadata':{'namespace':'app','name':'app'},'spec':{'replicas':1},'status':{'readyReplicas':0 if os.getenv('FAIL_CASE') else 1}},
         {'kind':'Deployment','metadata':{'namespace':'tailscale','name':'subnet-router'},'spec':{'replicas':0},'status':{}}]
elif 'pvc' in args: data = []
else: data = [{'spec':{'hostnames':['*.kleinsorge.dev','app.kleinsorge.dev','argocd-mcp.kleinsorge.dev']}}]
print(json.dumps({'items':data}))
""")
            curl = root / "curl"
            curl.write_text("""#!/usr/bin/env python3
import sys
url=sys.argv[-1]
if '*' in url: sys.exit(1)
print('401' if url.endswith('/mcp') else '200', end='')
""")
            kubectl.chmod(0o755)
            curl.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"])
            if failing:
                env["FAIL_CASE"] = "1"
            return subprocess.run(["bash", str(SCRIPT)], env=env, text=True, capture_output=True)

    def test_healthy_and_disabled_workloads(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("argocd-mcp.kleinsorge.dev/mcp", result.stdout)
        self.assertNotIn("Checking https://*", result.stdout)

    def test_app_failure_does_not_skip_endpoints(self):
        result = self.run_check(True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unavailable workloads", result.stderr)
        self.assertIn("Checking https://app.kleinsorge.dev/", result.stdout)
        self.assertIn("2 health check(s) failed", result.stderr)

if __name__ == "__main__":
    unittest.main()
