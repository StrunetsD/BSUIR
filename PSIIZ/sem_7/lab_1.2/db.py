"""Подключение к PostgreSQL."""

from __future__ import annotations

import os

import psycopg2


def admin_dsn(dbname: str = "postgres") -> str:
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "LabRootPass123!")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def user_dsn(username: str, password: str, dbname: str) -> str:
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    return f"host={host} port={port} dbname={dbname} user={username} password={password}"


def connect(dsn: str, autocommit: bool = False):
    conn = psycopg2.connect(dsn)
    conn.autocommit = autocommit
    return conn
