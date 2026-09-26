# Resilience actions outside GitOps

GitOps prevents configuration drift; it cannot repair failed hardware or
authenticate to the router. These actions are required to remove Freshlab's
remaining external single points of failure.

## Hardware

1. Replace Metal1's failed NVMe; do not return the old drive to service.
2. Reseat or replace Metal0's Ethernet cable and switch port until it
   negotiates at 1 Gb/s full duplex.
3. Before the next Metal3 reboot, cordon it and verify Longhorn replica
   health. Reseat its M.2 device, inspect the socket/standoff and airflow,
   update the OptiPlex 3080 BIOS, and stress-test with PCIe ASPM disabled.
   Replace the Patriot P300, then the motherboard/socket path, if PCIe RxErr
   events recur.
4. Before re-enabling a repaired node, burn it in, verify SMART/NVMe health,
   confirm `Ready`, and confirm Longhorn replicas are healthy.

## DNS and network management

In UniFi, remove or update the stale LAN static DNS record that sends
`*.kleinsorge.dev` (or individual Freshlab hosts) to `192.168.1.227`. The
shared public gateway address is `192.168.1.228`. Verify both the LAN resolver
and a public resolver return the intended address before declaring the route
healthy.

## Post-maintenance verification

After each action above, run `make smoke-test`, verify the quarterly restore
drill, and confirm the dashboard has no active Longhorn, SMART, temperature,
or link-speed alerts. Do not suppress an alert merely because a symptom has
cleared; record the cause and verification in the issue ledger.
