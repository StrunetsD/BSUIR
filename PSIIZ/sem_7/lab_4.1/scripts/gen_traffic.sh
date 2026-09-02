#!/usr/bin/env bash
# Плотный учебный трафик: нормальные запросы + сканы + SSH-брут.
# WEB_ROUNDS=30 SSH_ROUNDS=20 по умолчанию.
set -euo pipefail

WEB="${WEB_URL:-http://localhost:8080}"
SSH_HOST="${SSH_HOST:-127.0.0.1}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-labuser}"
WEB_ROUNDS="${WEB_ROUNDS:-30}"
SSH_ROUNDS="${SSH_ROUNDS:-20}"

echo "== Lab 4.1 traffic gen (web×${WEB_ROUNDS}, ssh×${SSH_ROUNDS}) =="

for i in $(seq 1 "$WEB_ROUNDS"); do
  curl -sS -o /dev/null "$WEB/" || true
  curl -sS -o /dev/null "$WEB/health" || true
  if (( i % 3 == 0 )); then
    curl -sS -o /dev/null -A "Mozilla/5.0" "$WEB/" || true
  fi
done
echo "OK normal web ×${WEB_ROUNDS}"

PROBES=(/admin /wp-login.php /.env /phpmyadmin /server-status /actuator /.git/config /xmlrpc.php /api/v1/users)
for path in "${PROBES[@]}"; do
  for _ in 1 2 3; do
    curl -sS -o /dev/null "$WEB$path" || true
  done
done
echo "OK probes"

for i in $(seq 1 80); do
  curl -sS -o /dev/null -A "sqlmap/1.0-lab41" "$WEB/unknown$i" || true
done
for i in $(seq 1 40); do
  curl -sS -o /dev/null -A "zgrab/0.x" "$WEB/scan$i" || true
done
echo "OK scanners"

if command -v sshpass >/dev/null 2>&1; then
  BAD_PASSES=(root admin test 123456 password qwerty letmein wrong1 wrong2 wrong3)
  for i in $(seq 1 "$SSH_ROUNDS"); do
    bad=${BAD_PASSES[$(( (i-1) % ${#BAD_PASSES[@]} ))]}
    sshpass -p "$bad" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      -o ConnectTimeout=3 \
      -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}" true 2>/dev/null \
      && echo "SSH unexpected OK" || echo "SSH fail #$i pass=$bad"
  done
  for u in root admin ubuntu; do
    sshpass -p x ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      -o ConnectTimeout=3 -p "$SSH_PORT" "${u}@${SSH_HOST}" true 2>/dev/null || echo "SSH deny user=$u"
  done
else
  echo "sshpass not found — skip live SSH fails (seed_history already fills auth.log)"
fi

echo "== done =="
