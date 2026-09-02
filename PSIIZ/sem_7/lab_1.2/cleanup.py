#!/usr/bin/env python3
"""
Лаб 1.2 — удаление ролей и базы PostgreSQL.

  python cleanup.py

Контейнер: docker compose --env-file /dev/null down -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from db import admin_dsn, connect

STATE_FILE = Path(__file__).parent / "lab_state.json"
LOG_FILE = Path(__file__).parent / "lab_1_2_results.log"


def main() -> int:
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    db_name = state.get("db_name", "psiiz_demo")
    users = list(state.get("users", {}).keys()) or ["lab_admin", "lab_user", "lab_guest"]

    try:
        conn = connect(admin_dsn(), autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
            print(f"[OK] база {db_name} удалена")
            for u in users:
                cur.execute(f"DROP ROLE IF EXISTS {u}")
                print(f"[OK] роль {u} удалена")
        conn.close()
    except Exception as e:
        print(f"[WARN] PostgreSQL: {e}", file=sys.stderr)

    for f in (STATE_FILE, LOG_FILE):
        if f.exists():
            f.unlink()
            print(f"[OK] удалён {f.name}")

    print("[INFO] контейнер: docker compose --env-file /dev/null down -v")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
