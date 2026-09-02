#!/usr/bin/env bash
# Разбор алертов Suricata (после атак).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVE="$ROOT/logs/suricata/eve.json"
FAST="$ROOT/logs/suricata/fast.log"
OUT="$ROOT/logs/after"
mkdir -p "$OUT"

echo "=== AFTER Suricata $(date -Iseconds) ===" | tee "$OUT/summary.txt"

if [[ -f "$FAST" ]]; then
  echo "--- fast.log (tail) ---" | tee -a "$OUT/summary.txt"
  tail -n 40 "$FAST" | tee -a "$OUT/summary.txt"
  echo "fast_alerts=$(grep -c . "$FAST" 2>/dev/null || echo 0)" | tee -a "$OUT/summary.txt"
fi

if [[ -f "$EVE" ]]; then
  echo "--- eve.json alerts by signature ---" | tee -a "$OUT/summary.txt"
  EVE="$EVE" python3 - <<'PY' | tee -a "$OUT/summary.txt"
import json, os
from collections import Counter
from pathlib import Path
eve = Path(os.environ["EVE"])
c = Counter()
srcs = Counter()
n = 0
for line in eve.read_text(errors="replace").splitlines():
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get("event_type") != "alert":
        continue
    n += 1
    sig = (o.get("alert") or {}).get("signature", "?")
    c[sig] += 1
    srcs[o.get("src_ip", "?")] += 1
print(f"alert_events={n}")
for sig, cnt in c.most_common(20):
    print(f"  {cnt:5d}  {sig}")
print("top src_ip:")
for ip, cnt in srcs.most_common(10):
    print(f"  {cnt:5d}  {ip}")
PY
fi

{
  echo "--- nginx after (suspicious sample) ---"
  grep -E 'sqlmap|wp-login|admin|\.env|zgrab' "$ROOT/logs/nginx/access.log" 2>/dev/null | tail -15 || true
  echo "--- auth Failed count ---"
  grep -c 'Failed password' "$ROOT/logs/auth.log" 2>/dev/null || echo 0
} | tee -a "$OUT/summary.txt"

echo "Saved $OUT/summary.txt"
