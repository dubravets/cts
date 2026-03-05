from fastapi.testclient import TestClient
from helpers import make_excel_bytes, make_word_bytes, upload_document

from app.main import app


def test_parse_profile_preview_is_stable_for_same_document() -> None:
    client = TestClient(app)
    doc_id = upload_document(
        client,
        doc_key="excel-spec",
        version="v1",
        filename="spec.xlsx",
        payload=make_excel_bytes(),
    )
    profile = client.post(
        "/api/v1/parsing/profiles",
        json={"name": "excel-default", "parser_type": "excel", "options": {}},
    )
    assert profile.status_code == 200, profile.text
    profile_id = profile.json()["id"]

    first = client.post(f"/api/v1/parsing/profiles/{profile_id}/preview/{doc_id}")
    second = client.post(f"/api/v1/parsing/profiles/{profile_id}/preview/{doc_id}")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_parse_profile_word_preview_extracts_mapping_candidates() -> None:
    client = TestClient(app)
    doc_id = upload_document(
        client,
        doc_key="word-spec",
        version="v1",
        filename="spec.docx",
        payload=make_word_bytes(),
    )
    profile = client.post(
        "/api/v1/parsing/profiles",
        json={"name": "word-default", "parser_type": "word", "options": {}},
    )
    assert profile.status_code == 200, profile.text
    profile_id = profile.json()["id"]

    preview = client.post(f"/api/v1/parsing/profiles/{profile_id}/preview/{doc_id}")
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["parser_type"] == "word"
    assert len(data["mapping_candidates"]) == 2
