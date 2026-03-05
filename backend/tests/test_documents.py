from fastapi.testclient import TestClient

from app.main import app


def test_upload_get_and_list_versions() -> None:
    client = TestClient(app)
    payload = {"doc_key": "backlight-spec", "version": "v1"}
    files = {
        "file": (
            "backlight.xlsx",
            b"binary-content",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    create_resp = client.post("/api/v1/documents", data=payload, files=files)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["doc_key"] == "backlight-spec"
    assert created["version"] == "v1"
    assert created["filename"] == "backlight.xlsx"
    assert created["size_bytes"] == len(b"binary-content")

    get_resp = client.get(f"/api/v1/documents/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created["id"]

    versions_resp = client.get("/api/v1/documents/backlight-spec/versions")
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 1
    assert versions[0]["version"] == "v1"


def test_upload_duplicate_version_returns_409() -> None:
    client = TestClient(app)
    payload = {"doc_key": "backlight-spec", "version": "v2"}
    files = {
        "file": (
            "backlight.xlsx",
            b"a",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    first = client.post("/api/v1/documents", data=payload, files=files)
    assert first.status_code == 200

    second = client.post("/api/v1/documents", data=payload, files=files)
    assert second.status_code == 409
