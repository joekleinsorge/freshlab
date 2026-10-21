#!/bin/sh
# Run once with sudo on Synology; cron thereafter needs no agent or login.
set -eu

if [ "$(id -u)" != 0 ]; then
    echo 'Run this installer with sudo on the Synology.' >&2
    exit 1
fi

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
test -x /var/packages/Docker/target/usr/bin/docker
test -f /volume1/docker/git/docker-compose.yml
test -d /etc/cron.d
install -d -m 700 /var/lib/freshlab-plex
install -d -m 755 /usr/local/sbin
install -o root -g root -m 755 "$source_dir/synology-plex-update.py" /usr/local/sbin/freshlab-plex-update.py

cat > /usr/local/sbin/freshlab-plex-update <<'RUNNER'
#!/bin/sh
/usr/bin/python3 /usr/local/sbin/freshlab-plex-update.py --apply > /var/lib/freshlab-plex/last-run.log 2>&1
result=$?
if [ "$result" -ne 0 ]; then
    /usr/syno/bin/synodsmnotify @administrators 'Plex update failed' 'Inspect /var/lib/freshlab-plex/last-run.log. Plex was not confirmed up to date and healthy.'
fi
exit "$result"
RUNNER
chown root:root /usr/local/sbin/freshlab-plex-update
chmod 755 /usr/local/sbin/freshlab-plex-update

cat > /etc/cron.d/freshlab-plex-update <<'CRON'
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/bin:/bin
0 5 * * * root /usr/local/sbin/freshlab-plex-update
CRON
chown root:root /etc/cron.d/freshlab-plex-update
chmod 644 /etc/cron.d/freshlab-plex-update

echo 'Installed daily Plex updates at 05:00 NAS local time, with DSM administrator notifications on failure.'
/usr/local/sbin/freshlab-plex-update
