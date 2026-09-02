#!/usr/bin/env bash
# Снимок «до» Suricata: только nginx/auth, без eve-алертов.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/logs/before"
mkdir -p "$OUT"

{
  echo "=== BEFORE Suricata $(date -Iseconds) ==="
  echo "--- access top paths ---"
  awk '{print $7}' "$ROOT/logs/nginx/access.log" 2>/dev/null | sort | uniq -c | sort -rn | head -20 || true
  echo "--- status ---"
  awk '{print $9}' "$ROOT/logs/nginx/access.log" 2>/dev/null | sort | uniq -c | sort -rn || true
  echo "--- auth Failed ---"
  grep -c 'Failed password' "$ROOT/logs/auth.log" 2>/dev/null || echo 0
} | tee "$OUT/summary.txt"

cp -f "$ROOT/logs/nginx/access.log" "$OUT/access.log" 2>/dev/null || true
cp -f "$ROOT/logs/auth.log" "$OUT/auth.log" 2>/dev/null || true
echo "Saved $OUT"
