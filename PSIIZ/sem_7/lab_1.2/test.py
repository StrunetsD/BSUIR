#!/usr/bin/env python3
"""
Лаб 1.2 — проверка политики доступа PostgreSQL.

  python test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from db import connect, user_dsn

STATE_FILE = Path(__file__).parent / "lab_state.json"
LOG_FILE = Path(__file__).parent / "lab_1_2_results.log"


def log(msg: str) -> None:
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def result(name: str, passed: bool, detail: str = "") -> None:
    status = "OK" if passed else "FAIL"
    line = f"[TEST] {name} | {status}"
    if detail:
        line += f" | {detail}"
    log(line)


def try_sql(username: str, password: str, dbname: str, sql: str) -> tuple[bool, str]:
    try:
        conn = connect(user_dsn(username, password, dbname))
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                cur.fetchall()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e).strip()


def main() -> int:
    if not STATE_FILE.exists():
        print(f"Сначала configure.py ({STATE_FILE} не найден)", file=sys.stderr)
        return 1

    LOG_FILE.write_text("", encoding="utf-8")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    db = state["db_name"]
    pw = state["users"]["lab_admin"]["password"]

    log("=== Проверка политики безопасности PostgreSQL ===")

    # --- admin ---
    ok, err = try_sql("lab_admin", pw, db, "SELECT * FROM public_data")
    result("admin: чтение public_data", ok, err)

    ok, err = try_sql("lab_admin", pw, db, "SELECT * FROM confidential_data")
    result("admin: чтение confidential_data", ok, err)

    ok, err = try_sql("lab_admin", pw, db, "INSERT INTO public_data (title, body) VALUES ('a','b')")
    result("admin: запись public_data", ok, err)

    ok, err = try_sql("lab_admin", pw, db, "INSERT INTO confidential_data (title, body) VALUES ('a','b')")
    result("admin: запись confidential_data", ok, err)

    ok, err = try_sql("lab_admin", pw, db, "CREATE TABLE admin_test (id int)")
    result("admin: CREATE TABLE", ok, err)
    if ok:
        try_sql("lab_admin", pw, db, "DROP TABLE admin_test")

    # --- user ---
    ok, err = try_sql("lab_user", pw, db, "SELECT * FROM public_data")
    result("user: чтение public_data", ok, err)

    ok, err = try_sql("lab_user", pw, db, "INSERT INTO public_data (title, body) VALUES ('u','u')")
    result("user: запись public_data", ok, err)

    ok, err = try_sql("lab_user", pw, db, "SELECT * FROM confidential_data")
    result("user: чтение confidential_data", ok, err)

    ok, err = try_sql("lab_user", pw, db, "INSERT INTO confidential_data (title, body) VALUES ('x','x')")
    result("user: запись confidential_data запрещена", not ok, err if not ok else "операция прошла")

    ok, err = try_sql("lab_user", pw, db, "CREATE TABLE user_test (id int)")
    result("user: CREATE TABLE запрещено", not ok, err if not ok else "операция прошла")

    # --- guest ---
    ok, err = try_sql("lab_guest", pw, db, "SELECT * FROM public_data")
    result("guest: чтение public_data", ok, err)

    ok, err = try_sql("lab_guest", pw, db, "INSERT INTO public_data (title, body) VALUES ('g','g')")
    result("guest: запись public_data запрещена", not ok, err if not ok else "операция прошла")

    ok, err = try_sql("lab_guest", pw, db, "SELECT * FROM confidential_data")
    result("guest: чтение confidential_data запрещено", not ok, err if not ok else "операция прошла")

    log(f"=== Готово, лог: {LOG_FILE} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
