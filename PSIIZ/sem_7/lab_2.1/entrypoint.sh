#!/bin/bash
set -e
mkdir -p "$(dirname "${DB_PATH:-/app/data/app.db}")"
# процесс Flask — от appuser (не root)
exec python3 /app/app.py
