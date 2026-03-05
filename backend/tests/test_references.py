from fastapi.testclient import TestClient

from app.main import app


def test_create_and_get_reference() -> None:
    client = TestClient(app)
    payload = {
        "doc_id": "doc-1",
        "location": "sheet:Backlight!A2",
        "excerpt": "Level 1 -> 500 nits",
    }

    create_resp = client.post("/api/v1/references", json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()

    get_resp = client.get(f"/api/v1/references/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["doc_id"] == "doc-1"


def test_get_missing_reference_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/references/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404
