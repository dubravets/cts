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


def _ensure_column(
    conn: sqlite3.Connection, *, table: str, column: str, column_definition: str
) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_definition}")


def _apply_runtime_migrations(conn: sqlite3.Connection) -> None:
    _ensure_column(
        conn, table="documents", column="doc_key", column_definition="TEXT NOT NULL DEFAULT ''"
    )
    _ensure_column(
        conn,
        table="documents",
        column="content_type",
        column_definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        conn, table="documents", column="size_bytes", column_definition="INTEGER NOT NULL DEFAULT 0"
    )
    _ensure_column(
        conn,
        table="documents",
        column="storage_path",
        column_definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        conn,
        table="requirements",
        column="status",
        column_definition="TEXT NOT NULL DEFAULT 'Draft'",
    )
    _ensure_column(
        conn,
        table="requirements",
        column="updated_at",
        column_definition="TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    _ensure_column(
        conn, table="spec_rules", column="name", column_definition="TEXT NOT NULL DEFAULT ''"
    )
    _ensure_column(
        conn, table="spec_rules", column="status", column_definition="TEXT NOT NULL DEFAULT 'Draft'"
    )
    _ensure_column(
        conn,
        table="spec_rules",
        column="updated_at",
        column_definition="TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    _ensure_column(
        conn,
        table="test_cases",
        column="case_type",
        column_definition="TEXT NOT NULL DEFAULT 'mapping'",
    )
    _ensure_column(
        conn, table="test_cases", column="source_spec_rule_id", column_definition="TEXT"
    )
    _ensure_column(
        conn,
        table="test_cases",
        column="to_confirm",
        column_definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        conn, table="test_cases", column="status", column_definition="TEXT NOT NULL DEFAULT 'Draft'"
    )
    _ensure_column(
        conn,
        table="test_cases",
        column="updated_at",
        column_definition="TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_doc_key_version
        ON documents(doc_key, version)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_references_doc_id
        ON "references"(doc_id)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parse_profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parser_type TEXT NOT NULL,
            options_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS baselines (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            label TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history_cases (
            id TEXT PRIMARY KEY,
            requirement_context TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_baselines_entity
        ON baselines(entity_type, entity_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_cases_context
        ON history_cases(requirement_context)
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
