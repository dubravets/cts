import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_bootstraps_schema(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "boot.db"
    monkeypatch.setenv("CTM_DB_PATH", str(db_path))

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'references'"
        ).fetchall()
    assert rows
