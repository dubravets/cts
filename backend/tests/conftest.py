from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def isolated_db_path(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[None, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("CTM_DB_PATH", str(db_path))
    yield
