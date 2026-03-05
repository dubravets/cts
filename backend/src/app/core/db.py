from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "cluster_test_mgmt.db"
DB_PATH_ENV = "CTM_DB_PATH"


def get_db_path() -> Path:
    raw = os.getenv(DB_PATH_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_DB_PATH


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> Path:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with _connect(db_path) as conn:
        conn.executescript(schema_sql)
    return db_path


def get_connection() -> sqlite3.Connection:
    db_path = init_db()
    return _connect(db_path)
