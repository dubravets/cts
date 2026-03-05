from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "cluster_test_mgmt.db"
DB_PATH_ENV = "CTM_DB_PATH"
DATA_DIR_ENV = "CTM_DATA_DIR"


def get_db_path() -> Path:
    raw = os.getenv(DB_PATH_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_DB_PATH


def get_data_dir() -> Path:
    raw = os.getenv(DATA_DIR_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_DB_PATH.parent


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _apply_runtime_migrations(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(documents)").fetchall()
    }
    if "doc_key" not in columns:
        conn.execute("ALTER TABLE documents ADD COLUMN doc_key TEXT NOT NULL DEFAULT ''")
    if "content_type" not in columns:
        conn.execute("ALTER TABLE documents ADD COLUMN content_type TEXT NOT NULL DEFAULT ''")
    if "size_bytes" not in columns:
        conn.execute("ALTER TABLE documents ADD COLUMN size_bytes INTEGER NOT NULL DEFAULT 0")
    if "storage_path" not in columns:
        conn.execute("ALTER TABLE documents ADD COLUMN storage_path TEXT NOT NULL DEFAULT ''")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_doc_key_version
        ON documents(doc_key, version)
        """
    )


def init_db() -> Path:
    db_path = get_db_path()
    get_data_dir().mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with _connect(db_path) as conn:
        conn.executescript(schema_sql)
        _apply_runtime_migrations(conn)
    return db_path


def get_connection() -> sqlite3.Connection:
    db_path = init_db()
    return _connect(db_path)
