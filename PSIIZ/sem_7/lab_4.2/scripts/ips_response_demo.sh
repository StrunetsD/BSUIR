#!/usr/bin/env bash
# «IPS-ответ»: по алертам Suricata собрать IP и показать блокировку (ufw/iptables demo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVE="$ROOT/logs/suricata/eve.json"
DENY="$ROOT/logs/after/deny_ips.txt"
mkdir -p "$ROOT/logs/after"

python3 - <<PY
import json
from pathlib import Path
from collections import Counter
eve = Path("$EVE")
c = Counter()
if eve.exists():
    for line in eve.read_text(errors="replace").splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("event_type") != "alert":
            continue
        ip = o.get("src_ip")
        if ip:
            c[ip] += 1
Path("$DENY").write_text(
    "\\n".join(f"{ip}  # alerts={n}" for ip, n in c.most_common()) + ("\\n" if c else ""),
    encoding="utf-8",
)
print(f"Wrote {len(c)} IPs to $DENY")
for ip, n in c.most_common(10):
    print(f"  would block {ip} (alerts={n})")
PY

echo
echo "Пример команд IPS на сервере (не выполняем автоматически на Mac Docker):"
echo "  iptables -A INPUT -s <IP> -j DROP"
echo "  # или fail2ban-client set sshd banip <IP>"
