#!/usr/bin/env bash
# Атаки / пробы против стенда 4.2 (после включения Suricata).
# Основной трафик — один контейнер в сети lab_42_default (видно Suricata на eth0).
set -euo pipefail
WEB="${WEB_URL:-http://localhost:8081}"
SSH_HOST="${SSH_HOST:-127.0.0.1}"
SSH_PORT="${SSH_PORT:-2223}"
SSH_USER="${SSH_USER:-labuser}"
NET="${COMPOSE_NET:-lab_42_default}"
TARGET="${ATTACK_TARGET:-http://server}"

echo "== Lab 4.2 attack traffic → docker:$TARGET + host:$WEB / $SSH_HOST:$SSH_PORT =="

docker run --rm --network "$NET" curlimages/curl:8.5.0 sh -c '
TARGET="'"$TARGET"'"
i=0
while [ "$i" -lt 10 ]; do
  curl -sS -o /dev/null "$TARGET/" || true
  curl -sS -o /dev/null "$TARGET/health" || true
  i=$((i+1))
done
for path in /admin /wp-login.php /.env /phpmyadmin /.git/config /xmlrpc.php; do
  j=0
  while [ "$j" -lt 5 ]; do
    curl -sS -o /dev/null "$TARGET$path" || true
    j=$((j+1))
  done
done
i=1
while [ "$i" -le 40 ]; do
  curl -sS -o /dev/null -A "sqlmap/1.0-lab42" "$TARGET/unknown$i" || true
  i=$((i+1))
done
i=1
while [ "$i" -le 20 ]; do
  curl -sS -o /dev/null -A "zgrab/0.x" "$TARGET/scan$i" || true
  i=$((i+1))
done
'

for path in /admin /wp-login.php /.env; do
  curl -sS -o /dev/null "$WEB$path" || true
done
curl -sS -o /dev/null -A "sqlmap/1.0-lab42" "$WEB/host-sqlmap" || true
curl -sS -o /dev/null -A "masscan/1.0" "$WEB/" || true

if command -v sshpass >/dev/null 2>&1; then
  for bad in root admin 123456 password wrong; do
    sshpass -p "$bad" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      -o ConnectTimeout=3 -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}" true 2>/dev/null || echo "SSH fail $bad"
  done
fi

echo "== done =="
