# Storage isolation hardware specification

Issue: https://github.com/joekleinsorge/freshlab/issues/200

Prices checked **2026-10-19**, USD, before tax, shipping, installation, and any
missing Dell cables/caddies. Supplier starting prices are marked as indicative;
they are not confirmed checkout quotes. No purchases have been made.

## Existing hardware and compatibility

All four hosts identify as Dell OptiPlex 3080. Metal1 reports an i3-10100T and
board 006K82, consistent with the Micro family; SMBIOS reports only `Desktop`.
The exact chassis and internal cable/caddy contents must be checked physically
before ordering. Metal1/2/3 have Patriot P300 512 GB NVMe root disks. Metal0
uses a 500 GB mechanical SATA disk. Metal2 exposes an AHCI SATA controller.

Dell documents an M.2 2230/2280 NVMe drive plus one 2.5-inch SATA drive for the
[3080 Micro](https://www.dell.com/support/manuals/en-sg/optiplex-3080-micro/optiplex3080_micro_specs/storage?guid=guid-6dd90062-b4b7-4476-96c5-8d6b318fcd83&lang=en-us).
Use an internal 7 mm 2.5-inch SATA SSD and the correct Dell caddy/cable. Confirm
the M.2 heatsink clears the enclosure and SATA tray. PCIe 4.0 drives will operate
at the host's negotiated link speed; full Gen4 bandwidth is not required.
Do not order U.2/U.3, SAS, M.2 SATA, or 22110 drives as substitutes for 2280 NVMe.

## Recommended layout

Keep three control-plane members. Each node gets two separate physical devices:

- M.2 NVMe: Ubuntu, k3s/container images, and local etcd where applicable.
- Internal SATA SSD: Longhorn data only, mounted by filesystem UUID at
  `/var/lib/longhorn` before Longhorn starts.

An unmounted storage disk must prevent Longhorn startup/scheduling; otherwise
an empty mount directory could silently send replicas back onto the root disk.
Partitions on one drive do not isolate I/O or physical-device failures.

The control-plane root replacement candidate is the
[Kingston DC2000B 960 GB, SEDC2000BM8/960G](https://www.kingston.com/en/ssd/dc2000b-data-center-solid-state-drive),
M.2 2280 with hardware power-loss protection. Verify its factory heatsink
clearance and sustained thermals in this chassis. Prefer the 960 GB model to
retain image-cache headroom; a smaller boot drive needs a separate capacity review.

For Longhorn, request a **new 1.92 TB Micron 5400 PRO, 2.5-inch 7 mm SATA**, with
documented manufacturer warranty and the exact SKU confirmed by the supplier.
[Micron's product brief](https://www.micron.com/content/dam/micron/global/public/products/product-flyer/5400-product-brief.pdf)
specifies power-loss protection; its
[part catalog](https://www.micron.com/products/storage/ssd/data-center-ssd/5400-sata-ssd/part-catalog)
distinguishes interface, capacity, and encryption variants. Select the correct
SATA SKU rather than relying on a reseller's generic family description.

## Current price evidence and budget

| Item | Unit price observed | Quantity | Extended | Price type/source |
|---|---:|---:|---:|---|
| Kingston DC2000B 960 GB NVMe | $195.99 | 4 | $783.96 | [Newegg listed retail](https://www.newegg.com/p/2U3-000W-00008?item=2U3-000W-00008), sold/shipped by Newegg |
| Micron 5400 PRO 1.92 TB SATA | from $255 | 4 | from $1,020 | [Supplier capacity table](https://www.nexus-compute.com/products/components/micron-5400-pro-960gb), indicative, written quote required |
| Dell caddies/cables/thermal parts | not quoted | as inspected | not included | Exact chassis/parts verification required |

**Full four-node drive budget: from $1,803.96**, subject to the SATA quote and
physical fit verification. Adding one matched SATA spare raises that starting
budget to $2,058.96. These figures are estimates, not a purchase authorization.

A staged first purchase is the three control-plane SATA drives, from **$765**,
plus required mounting parts. This immediately separates Longhorn from etcd on
those hosts while retaining the currently installed NVMe drives under monitoring.
Replace metal2/metal3's NVMe path next if PCIe errors or long fsyncs recur after
storage separation; validate each new drive before buying the remaining set.

For comparison, a [Kingston DC600M 960 GB SATA retail listing](https://www.newegg.com/kingston-960gb/p/0D9-001B-00586)
currently shows marketplace offers around $689.24. That is poor value relative
to the indicative Micron quote; do not substitute it automatically. Supplier
descriptions and prices differ substantially, so obtain a written exact-SKU,
new-condition, warranty, stock, and delivered-price confirmation before purchase.

## Capacity acceptance

Four 1.92 TB disks provide 7.68 TB raw decimal capacity. At a 30% headroom target,
about 5.38 TB remains before replication and snapshot overhead. With two replicas
this is at most about 2.69 TB of logical data before snapshots, filesystem
overhead, and failure/rebuild reserves. It is not an application allocation budget.

Admission must use the worst remaining-node placement after any one host loss,
including physical snapshot growth and temporary coalescing/rebuild space. The
Frigate incident demonstrates that a 150 GiB PVC can occupy over 350 GiB per
replica. Keep disposable recordings separate from important databases/configuration.

## Migration and verification

1. Confirm current backups and an off-node etcd snapshot. Complete the current
   snapshot purge and restore metal2's original ext4 reserve first.
2. Inventory actual devices, UUIDs, bays, firmware, and cables. Burn in new drives
   on disposable storage outside the live data path; do not run destructive fio
   against a mounted filesystem or existing replica.
3. Work on one node at a time. Check API/etcd health and two surviving control-plane
   members. Use `metal/rolling-node-maintenance.sh` to evacuate safely. Never
   power off the sole replica of an important volume.
4. Add UUID-based mounts and Longhorn disk definitions through Ansible/GitOps.
   The role must refuse unexpected filesystems/devices and refuse to format a
   disk containing data. Do not implement disk formatting from guessed names.
5. Use Longhorn's supported disk/replica migration. Do not copy live replica
   directories as the final migration method. Retain the old disk until data,
   replicas, and restoration have been verified.
6. Replace a root drive only after evacuation; rebuild/rejoin the existing etcd
   cluster one member at a time. Do not form a new control plane.
7. Reboot the migrated node to prove mount ordering, then require clean SMART,
   no new PCIe RxErr, acceptable etcd fsync latency under representative load,
   no node pressure, and healthy independent replicas before the next node.
8. Run smoke checks and a disposable application restore. Observe for 24 hours
   between control-plane hardware migrations, then complete a 30-day stability review.

Hardware installation, a UPS/power inspection, NAS snapshot/off-site policy,
and reseating/airflow work remain physical or external-system tasks. This spec
does not claim those tasks have been completed.
