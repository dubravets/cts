from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def isolated_db_path(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[None, None, None]:
    data_dir = tmp_path / "data"
    db_path = data_dir / "test.db"
    monkeypatch.setenv("CTM_DB_PATH", str(db_path))
    monkeypatch.setenv("CTM_DATA_DIR", str(data_dir))
    yield
