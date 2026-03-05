from fastapi.testclient import TestClient
from helpers import create_reference, make_excel_bytes, upload_document

from app.main import app


def test_requirement_and_spec_rule_crud_with_references() -> None:
    client = TestClient(app)
    doc_id = upload_document(
        client,
        doc_key="knowledge-spec",
        version="v1",
        filename="spec.xlsx",
        payload=make_excel_bytes(),
    )
    ref_id = create_reference(
        client,
        doc_id=doc_id,
        location="sheet:Backlight!A2",
        excerpt="L1 -> 500",
    )

    req_create = client.post(
        "/api/v1/knowledge/requirements",
        json={"statement": "L1 should map to expected nits", "reference_ids": [ref_id]},
    )
    assert req_create.status_code == 200, req_create.text
    requirement_id = req_create.json()["id"]

    req_update = client.put(
        f"/api/v1/knowledge/requirements/{requirement_id}",
        json={"statement": "L2 should map to expected nits", "reference_ids": [ref_id]},
    )
    assert req_update.status_code == 200
    assert req_update.json()["statement"] == "L2 should map to expected nits"
    assert req_update.json()["reference_ids"] == [ref_id]

    spec_create = client.post(
        "/api/v1/knowledge/spec-rules",
        json={
            "name": "backlight mapping",
            "rule_type": "mapping",
            "expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 500, "expected_source": "spec_rule"},
                ]
            },
            "reference_ids": [ref_id],
        },
    )
    assert spec_create.status_code == 200, spec_create.text
    spec_rule_id = spec_create.json()["id"]

    spec_get = client.get(f"/api/v1/knowledge/spec-rules/{spec_rule_id}")
    assert spec_get.status_code == 200
    assert spec_get.json()["reference_ids"] == [ref_id]

    spec_update = client.put(
        f"/api/v1/knowledge/spec-rules/{spec_rule_id}",
        json={
            "name": "backlight mapping v2",
            "rule_type": "mapping",
            "expression": {
                "mappings": [
                    {"level": "L2", "expected_nits": 800, "expected_source": "spec_rule"},
                ]
            },
            "reference_ids": [ref_id],
        },
    )
    assert spec_update.status_code == 200
    assert spec_update.json()["name"] == "backlight mapping v2"

    req_delete = client.delete(f"/api/v1/knowledge/requirements/{requirement_id}")
    assert req_delete.status_code == 200
    spec_delete = client.delete(f"/api/v1/knowledge/spec-rules/{spec_rule_id}")
    assert spec_delete.status_code == 200
