#!/usr/bin/env bash
# Сводка по логам контейнера psiiz-lab41-server
set -euo pipefail

C="${CONTAINER:-psiiz-lab41-server}"

echo "=== nginx access (top paths) ==="
docker exec "$C" sh -c 'awk "{print \$7}" /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn | head -20'

echo
echo "=== nginx access (top status codes) ==="
docker exec "$C" sh -c 'awk "{print \$9}" /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn'

echo
echo "=== nginx: suspicious UA / probes (sample) ==="
docker exec "$C" sh -c 'grep -E "sqlmap|wp-login|admin|\.env|phpmyadmin" /var/log/nginx/access.log 2>/dev/null | tail -30' || true

echo
echo "=== auth.log: SSH Failed / Invalid (sample) ==="
docker exec "$C" sh -c 'grep -E "Failed|Invalid|Accepted|Disconnected" /var/log/auth.log 2>/dev/null | tail -40' || true

echo
echo "=== raw tails ==="
echo "--- access.log ---"
docker exec "$C" tail -n 15 /var/log/nginx/access.log 2>/dev/null || true
echo "--- auth.log ---"
docker exec "$C" tail -n 15 /var/log/auth.log 2>/dev/null || true
