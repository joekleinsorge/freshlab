# Freshlab metal provisioning

Freshlab nodes run Ubuntu Server 26.04 LTS on amd64. The supported topology is
three k3s control-plane nodes (`metal1` through `metal3`) and one worker
(`metal0`). Keeping three control-plane nodes preserves an odd-sized etcd
quorum while still using all four machines.

## Install Ubuntu

Install Ubuntu Server 26.04 LTS with these choices on each Dell OptiPlex:

- UEFI boot mode
- Minimal Ubuntu Server installation
- Guided use of the entire NVMe disk without disk encryption
- OpenSSH server enabled
- Hostname matching the inventory (`metal0`, `metal1`, `metal2`, or `metal3`)
- Initial administrator account named `lab`
- The existing `~/.ssh/id_ed25519.pub` key authorized for `lab`

Use DHCP reservations or static network configuration for the addresses in
`inventories/prod.yml`. After installation, verify the actual disk and network
interface names with:

```shell
lsblk
ip -br link
```

The Dell OptiPlex 3080 systems currently use `/dev/nvme0n1` and `enp2s0`. If a
machine differs, update its inventory entry before provisioning.

## Validate a newly installed node

From this directory, validate connectivity, Ubuntu version, sudo access,
hardware sizing, interface name, and disk name:

```shell
make preflight ANSIBLE_LIMIT=metal0 ANSIBLE_EXTRA_ARGS=--ask-become-pass
```

The password prompt is for the `lab` account's sudo password. Passwordless sudo
can be configured separately, but is not required.

## Provision the cluster

Prepare or update Ubuntu hosts without installing or changing k3s:

```shell
make prepare ANSIBLE_LIMIT=metal0,metal2 ANSIBLE_EXTRA_ARGS=--ask-become-pass
```

With the documented passwordless sudo rule in place, omit
`ANSIBLE_EXTRA_ARGS`.

Run the complete provisioning workflow only when at least one existing
control-plane node is healthy:

```shell
make cluster ANSIBLE_EXTRA_ARGS=--ask-become-pass
```

To add a rebuilt worker while using a specific healthy control-plane node for
the cluster token, limit the run to both machines:

```shell
make cluster ANSIBLE_LIMIT=metal3,metal0 ANSIBLE_EXTRA_ARGS=--ask-become-pass
```

Do not reinstall or reinitialize multiple control-plane nodes at once. Preserve
at least two healthy etcd members, or a tested etcd snapshot, throughout a
rolling operating-system migration.

## Ubuntu host behavior

Provisioning installs the k3s, Longhorn, and NFS host dependencies; disables
swap and UFW; retains AppArmor; enables Ubuntu unattended security updates; and
leaves reboots to the cluster's coordinated reboot tooling.

The NAS share is configured as a non-blocking systemd automount. A NAS outage
therefore does not prevent a node from booting.
