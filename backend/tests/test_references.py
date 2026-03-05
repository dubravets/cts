from fastapi.testclient import TestClient

from app.main import app


def _create_document(client: TestClient) -> str:
    payload = {"doc_key": "backlight-spec", "version": "v-ref"}
    files = {
        "file": (
            "reference-source.xlsx",
            b"sheet-content",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/documents", data=payload, files=files)
    assert response.status_code == 200
    return response.json()["id"]


def test_create_and_get_reference() -> None:
    client = TestClient(app)
    doc_id = _create_document(client)
    payload = {
        "doc_id": doc_id,
        "location": "sheet:Backlight!A2",
        "excerpt": "Level 1 -> 500 nits",
    }

    create_resp = client.post("/api/v1/references", json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["doc_id"] == doc_id
    assert "created_at" in created

    get_resp = client.get(f"/api/v1/references/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["doc_id"] == doc_id


def test_get_missing_reference_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/references/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_create_reference_requires_existing_document() -> None:
    client = TestClient(app)
    payload = {
        "doc_id": "11111111-1111-1111-1111-111111111111",
        "location": "sheet:Backlight!A2",
        "excerpt": "Level 1 -> 500 nits",
    }
    response = client.post("/api/v1/references", json=payload)
    assert response.status_code == 404
