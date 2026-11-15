#!/bin/sh
set -eu
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo 'Install Docker Engine and Compose first.'; exit 1; }
docker compose version >/dev/null
if [ ! -f .env ]; then
  python3 - <<'PY'
from pathlib import Path
import socket
for port in range(8095,8196):
    with socket.socket() as s:
        try:s.bind(('0.0.0.0',port))
        except OSError:continue
        Path('.env').write_text(f'WEB_PORT={port}\nBIND_ADDRESS=0.0.0.0\n');print('Selected port:',port);break
else:raise SystemExit('No available port in 8095–8195')
PY
fi
mkdir -p data recordings cache updates
chown 10001:10001 data recordings cache updates
chmod 700 data recordings cache updates
docker compose up -d --build
echo 'Open http://SERVER_IP:PORT and create the first administrator account.'

if command -v systemctl >/dev/null && [ -d /run/systemd/system ]; then
  sh deployment/install-updater.sh "$PWD"
else
  echo "Web updates require Linux systemd; manual Docker updates remain available."
fi
