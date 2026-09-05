#!/usr/bin/env bash
set -euo pipefail

# Prepare one node at a time for hardware replacement. This script never reboots
# or powers off a node; the operator performs the physical work after evacuation.

usage() {
  echo "Usage: $0 check | evacuate NODE | resume NODE" >&2
  exit 2
}

need() {
  command -v "$1" >/dev/null || { echo "missing required command: $1" >&2; exit 1; }
}

ready_nodes() {
  kubectl get nodes -o json | jq -r '[.items[] | select(any(.status.conditions[]?; .type == "Ready" and .status == "True")) | .metadata.name] | .[]'
}

volume_failures() {
  kubectl -n longhorn get volumes.longhorn.io -o json | jq -r '
    .items[]
    | select(.status.robustness != "healthy" or .status.state != "attached")
    | [.metadata.name, (.status.robustness // "-"), (.status.state // "-")] | @tsv'
}

control_plane_ready_count() {
  kubectl get nodes -l node-role.kubernetes.io/control-plane -o json | jq '[.items[] | select(any(.status.conditions[]?; .type == "Ready" and .status == "True"))] | length'
}

check() {
  local ready masters failures
  ready="$(ready_nodes)"
  masters="$(control_plane_ready_count)"
  failures="$(volume_failures)"

  echo "Ready nodes:"
  printf '%s\n' "$ready"
  echo "Ready control-plane nodes: $masters"

  if [[ "$masters" -lt 2 ]]; then
    echo "STOP: fewer than two control-plane nodes are Ready." >&2
    return 1
  fi
  if [[ -n "$failures" ]]; then
    echo "STOP: Longhorn has unhealthy or detached volumes:" >&2
    printf '%s\n' "$failures" >&2
    return 1
  fi
}

evacuate() {
  local node="$1"
  kubectl get node "$node" >/dev/null
  check

  if ! ready_nodes | grep -qx "$node"; then
    echo "STOP: target node $node is not Ready." >&2
    return 1
  fi

  kubectl cordon "$node"
  kubectl -n longhorn patch node.longhorn.io "$node" --type=merge \
    -p '{"spec":{"allowScheduling":false,"evictionRequested":true}}'

  echo "Waiting for Longhorn replicas to leave $node..."
  while kubectl -n longhorn get replicas.longhorn.io -o json \
    | jq -e --arg node "$node" '[.items[] | select(.spec.nodeID == $node and .status.currentState != "stopped")] | length > 0' >/dev/null; do
    sleep 10
  done

  kubectl drain "$node" --ignore-daemonsets --delete-emptydir-data --grace-period=60 --timeout=15m
  echo "Node $node is cordoned, drained, and Longhorn-evacuated. Replace the drive now; do not remove the node object."
}

resume() {
  local node="$1"
  kubectl get node "$node" >/dev/null
  kubectl uncordon "$node"
  kubectl -n longhorn patch node.longhorn.io "$node" --type=merge \
    -p '{"spec":{"allowScheduling":true,"evictionRequested":false}}'
  echo "Node $node was made schedulable. Run the preflight and verify Longhorn health before proceeding to another node."
}

need kubectl
need jq

case "${1:-}" in
  check) check ;;
  evacuate) [[ $# -eq 2 ]] || usage; evacuate "$2" ;;
  resume) [[ $# -eq 2 ]] || usage; resume "$2" ;;
  *) usage ;;
esac
