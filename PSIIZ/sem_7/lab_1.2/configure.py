#!/usr/bin/env python3
"""
Лаб 1.2 — настройка политики доступа PostgreSQL.

Перед запуском:
  1. docker compose --env-file /dev/null up -d
  2. pip install -r requirements.txt
  3. python configure.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path 

from db import admin_dsn, connect, user_dsn

DB_NAME = "psiiz_demo"
USER_PASS = "LabUserPass123!"
STATE_FILE = Path(__file__).parent / "lab_state.json"

USERS = [
    ("lab_admin", "admin", "SUPERUSER CREATEDB CREATEROLE"),
    ("lab_user", "user", ""),
    ("lab_guest", "guest", ""),
]


def run_sql(conn, sql: str, params=None) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def main() -> int:
    conn = connect(admin_dsn(), autocommit=True)
    print("[OK] подключение к PostgreSQL (postgres)")

    for username, role, attrs in USERS:
        run_sql(conn, f"DROP ROLE IF EXISTS {username}")
        extra = f" {attrs}" if attrs else ""
        run_sql(
            conn,
            f"CREATE ROLE {username} WITH LOGIN PASSWORD %s{extra}",
            (USER_PASS,),
        )
        print(f"[OK] роль {username} ({role})")

    run_sql(conn, f"DROP DATABASE IF EXISTS {DB_NAME}")
    run_sql(conn, f"CREATE DATABASE {DB_NAME} OWNER lab_admin")
    print(f"[OK] база {DB_NAME}")

    conn.close()

    conn = connect(admin_dsn(DB_NAME), autocommit=True)
    run_sql(
        conn,
        """
        CREATE TABLE public_data (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL
        );
        CREATE TABLE confidential_data (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL
        );
        INSERT INTO public_data (title, body) VALUES
            ('public-1', 'открытые данные'),
            ('public-2', 'ещё открытые данные');
        INSERT INTO confidential_data (title, body) VALUES
            ('secret-1', 'конфиденциально');
        """,
    )
    print("[OK] таблицы public_data, confidential_data")

    # admin — полный доступ (owner + superuser)
    run_sql(conn, "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lab_admin")
    run_sql(conn, "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lab_admin")

    # user — частичные права: всё на public, только чтение confidential
    run_sql(conn, "GRANT SELECT, INSERT, UPDATE, DELETE ON public_data TO lab_user")
    run_sql(conn, "GRANT USAGE, SELECT ON SEQUENCE public_data_id_seq TO lab_user")
    run_sql(conn, "GRANT SELECT ON confidential_data TO lab_user")

    # guest — только чтение public_data
    run_sql(conn, "GRANT SELECT ON public_data TO lab_guest")

    run_sql(conn, "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO lab_guest")
    conn.close()
    print("[OK] GRANT: lab_user=write public/read secret, lab_guest=read public")

    state = {
        "db_name": DB_NAME,
        "db_host": "localhost",
        "db_port": 5432,
        "users": {
            u: {"password": USER_PASS, "role": r}
            for u, r, _ in USERS
        },
    }
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    STATE_FILE.chmod(0o600)
    print(f"[OK] состояние: {STATE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
