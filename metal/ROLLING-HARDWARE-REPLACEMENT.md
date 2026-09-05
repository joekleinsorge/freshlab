# Rolling hard-drive replacement

Replace one node at a time. Do not start a new replacement while any other
node is `NotReady`, while fewer than two control-plane nodes are healthy, or
while Longhorn reports a degraded, faulted, or detached volume.

## Before the first node

1. Restore `metal1` to `Ready`; it is currently `NotReady` and cordoned.
2. Confirm the Prometheus Longhorn volume is healthy. It is currently faulted
   and detached, so the cluster is not yet safe for another storage outage.
3. Run the read-only gate:

   ```shell
   ./metal/rolling-node-maintenance.sh check
   ```

## For each node

From the repository root:

```shell
./metal/rolling-node-maintenance.sh evacuate metal0
```

After the command reports that the node is drained and Longhorn-evacuated,
replace the drive and reprovision only that node:

```shell
make -C metal preflight ANSIBLE_LIMIT=metal0
make -C metal prepare ANSIBLE_LIMIT=metal0
make -C metal cluster ANSIBLE_LIMIT=metal3,metal0
```

Use a healthy control-plane node in the `cluster` limit. Never rebuild two
control-plane nodes together; preserve two healthy etcd members.

After the node rejoins, make it schedulable again and verify recovery:

```shell
./metal/rolling-node-maintenance.sh resume metal0
./metal/rolling-node-maintenance.sh check
kubectl get nodes
kubectl -n longhorn get volumes
```

Only then continue to the next node.

## Important storage rule

Do not delete Longhorn volumes, replicas, PVCs, or the Kubernetes node object
as part of drive replacement. The procedure disables scheduling and requests
replica eviction, then reuses the node identity after reprovisioning. A volume
that cannot evacuate is a stop condition requiring storage recovery first.
