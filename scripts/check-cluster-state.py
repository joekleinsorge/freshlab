#!/usr/bin/env python3
"""Read-only reliability checks beyond Kubernetes Ready/Longhorn healthy."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs/operations/reliability-policy.json"


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def assess(state, policy, now):
    failures = []
    nodes = {n["metadata"]["name"]: n for n in state["nodes"]}
    for name in policy["expected_nodes"]:
        conditions = {c["type"]: c["status"] for c in nodes.get(name, {}).get("status", {}).get("conditions", [])}
        if conditions.get("Ready") != "True":
            failures.append(f"Node {name} is missing or not Ready")
        for pressure in ("DiskPressure", "MemoryPressure", "PIDPressure"):
            if conditions.get(pressure) != "False":
                failures.append(f"Node {name}: {pressure}={conditions.get(pressure, 'missing')}")
    claims = {(p["metadata"]["namespace"], p["metadata"]["name"]): p for p in state["pvc"]}
    volumes = {v["metadata"]["name"]: v for v in state["volumes.longhorn.io"]}
    sources = {(s["metadata"]["namespace"], s["metadata"]["name"]): s for s in state["replicationsources.volsync.backube"]}
    required_volumes = set()
    for item in policy["volumes"]:
        key = (item["namespace"], item["pvc"])
        label = "/".join(key)
        claim = claims.get(key)
        if not claim or claim.get("status", {}).get("phase") != "Bound":
            failures.append(f"Required PVC {label} is missing or unbound")
            continue
        volume_name = claim.get("spec", {}).get("volumeName")
        required_volumes.add(volume_name)
        volume = volumes.get(volume_name, {})
        minimum = item["min_replicas"]
        if volume.get("spec", {}).get("numberOfReplicas", 0) < minimum:
            failures.append(f"PVC {label}: configured replicas below policy minimum {minimum}")
        replica_nodes = {
            r["spec"].get("nodeID") for r in state["replicas.longhorn.io"]
            if r["spec"].get("volumeName") == volume_name
            and r["spec"].get("healthyAt") and not r["spec"].get("failedAt")
            and r["spec"].get("nodeID")
        }
        if len(replica_nodes) < minimum:
            failures.append(f"PVC {label}: only {len(replica_nodes)} independent healthy replica(s), need {minimum}")
        source = sources.get((item["namespace"], item["backup_source"]))
        if not source:
            failures.append(f"PVC {label}: required backup source is missing")
            continue
        if source["spec"].get("sourcePVC") != item["pvc"]:
            failures.append(f"PVC {label}: backup points at another PVC")
        if source["spec"].get("paused", False):
            failures.append(f"PVC {label}: backups are paused")
        status = source.get("status", {})
        trigger = source["spec"].get("trigger", {})
        if (trigger.get("manual") and trigger.get("schedule")
                and status.get("lastManualSync") == trigger["manual"]):
            failures.append(f"PVC {label}: completed manual trigger blocks scheduled backups")
        last = status.get("lastSyncTime")
        try:
            age = (now - timestamp(last)).total_seconds() if last else float("inf")
        except (TypeError, ValueError):
            age = float("inf")
        if age < -300 or age > item["max_backup_age_hours"] * 3600:
            failures.append(f"PVC {label}: backup is missing, stale, or has an invalid future timestamp")
        result = status.get("latestMoverStatus", {}).get("result")
        if result and result != "Successful":
            failures.append(f"PVC {label}: latest backup result is {result}")
    for snapshot in state["snapshots.longhorn.io"]:
        error = snapshot.get("status", {}).get("error")
        volume_name = snapshot.get("spec", {}).get("volume")
        active = volumes.get(volume_name, {}).get("status", {}).get("state") == "attached"
        if error and (active or volume_name in required_volumes):
            failures.append(f"Snapshot {snapshot['metadata']['name']}: {error}")
    for engine in state["engines.longhorn.io"]:
        for purge in (engine.get("status", {}).get("purgeStatus") or {}).values():
            if purge.get("error"):
                failures.append(f"Engine {engine['metadata']['name']}: snapshot purge failed: {purge['error']}")
    return failures


def collect():
    state = {}
    resources = ("nodes", "pvc", "volumes.longhorn.io", "replicas.longhorn.io",
                 "replicationsources.volsync.backube", "snapshots.longhorn.io", "engines.longhorn.io")
    for resource in resources:
        command = ["kubectl", "--request-timeout=15s", "get", resource, "-A", "-o", "json"]
        result = subprocess.run(command, text=True, capture_output=True, timeout=20, check=True)
        state[resource] = json.loads(result.stdout)["items"]
    return state


def main():
    os.environ.setdefault("KUBECONFIG", str(ROOT / "metal/kubeconfig.yaml"))
    try:
        policy = json.loads(Path(os.getenv("FRESHLAB_HEALTH_POLICY", str(POLICY))).read_text())
        failures = assess(collect(), policy, dt.datetime.now(dt.timezone.utc))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Reliability checks could not complete: {error}", file=sys.stderr)
        return 1
    if failures:
        print("Reliability policy failures:\n" + "\n".join(f" - {f}" for f in failures), file=sys.stderr)
        return 1
    print("Node pressure, replica policy, backup freshness, and snapshot checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
