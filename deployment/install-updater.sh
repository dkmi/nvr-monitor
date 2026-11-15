#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run this installer as root.'; exit 1; }
command -v systemctl >/dev/null || { echo 'The host updater requires systemd.'; exit 1; }
project=$(cd "${1:-.}" && pwd -P)
# Keep systemd unit arguments literal; supported installation paths have no whitespace.
case "$project" in *[!a-zA-Z0-9_./-]*) echo 'Unsupported project path'; exit 1;; esac
[ -f "$project/compose.yaml" ] && [ -f "$project/updater/host.py" ]
mkdir -p "$project/updates"
chown 10001:10001 "$project/updates"
chmod 700 "$project/updates"
install -o root -g root -m 755 "$project/updater/host.py" /usr/local/lib/nvr-monitor-updater.py
cat > /etc/systemd/system/nvr-monitor-updater.service <<UNIT
[Unit]
Description=NVR Monitor official release updater
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service
[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/nvr-monitor-updater.py --project $project
Restart=on-failure
RestartSec=5
UMask=0077
TimeoutStopSec=240
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable nvr-monitor-updater.service
systemctl restart nvr-monitor-updater.service
echo 'Host updater enabled. Only official stable releases can be requested.'
