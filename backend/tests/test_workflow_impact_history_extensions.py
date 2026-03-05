from fastapi.testclient import TestClient
from helpers import create_reference, make_excel_bytes, upload_document

from app.main import app


def test_workflow_baseline_impact_history_and_extensions() -> None:
    client = TestClient(app)
    doc_id = upload_document(
        client,
        doc_key="full-spec",
        version="v1",
        filename="full.xlsx",
        payload=make_excel_bytes(),
    )
    ref_id = create_reference(
        client,
        doc_id=doc_id,
        location="sheet:Backlight!A2",
        excerpt="L1 -> 500",
    )

    spec_a = client.post(
        "/api/v1/knowledge/spec-rules",
        json={
            "name": "rule-a",
            "rule_type": "mapping",
            "expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 500, "expected_source": "spec_rule"},
                    {"level": "L2", "expected_nits": 800, "expected_source": "spec_rule"},
                ],
                "thresholds": [
                    {
                        "name": "min-backlight",
                        "comparator": ">=",
                        "value": 450,
                        "expected_source": "spec_rule",
                    }
                ],
                "invalid_levels": [{"level": "L99", "reason": "unsupported level"}],
            },
            "reference_ids": [ref_id],
        },
    )
    assert spec_a.status_code == 200, spec_a.text
    spec_a_id = spec_a.json()["id"]

    spec_b = client.post(
        "/api/v1/knowledge/spec-rules",
        json={
            "name": "rule-b",
            "rule_type": "mapping",
            "expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 550, "expected_source": "spec_rule"},
                    {"level": "L3", "expected_nits": 900, "expected_source": "spec_rule"},
                ]
            },
            "reference_ids": [ref_id],
        },
    )
    assert spec_b.status_code == 200, spec_b.text
    spec_b_id = spec_b.json()["id"]

    generated_mapping = client.post(f"/api/v1/generation/spec-rules/{spec_a_id}/mapping-cases")
    assert generated_mapping.status_code == 200
    mapping_cases = generated_mapping.json()["cases"]

    generated_threshold = client.post(f"/api/v1/generation/spec-rules/{spec_a_id}/threshold-cases")
    assert generated_threshold.status_code == 200
    assert len(generated_threshold.json()["cases"]) == 1
    assert generated_threshold.json()["cases"][0]["case_type"] == "threshold"

    generated_invalid = client.post(f"/api/v1/generation/spec-rules/{spec_a_id}/invalid-cases")
    assert generated_invalid.status_code == 200
    assert len(generated_invalid.json()["cases"]) == 1
    assert generated_invalid.json()["cases"][0]["case_type"] == "invalid"

    transition = client.post(
        f"/api/v1/workflow/spec_rule/{spec_a_id}/transition",
        json={"to_state": "Review", "actor": "qa-bot"},
    )
    assert transition.status_code == 200, transition.text
    assert transition.json()["state"] == "Review"

    baseline = client.post(
        f"/api/v1/workflow/spec_rule/{spec_a_id}/baseline",
        json={"label": "pre-publish", "actor": "qa-bot"},
    )
    assert baseline.status_code == 200, baseline.text
    assert baseline.json()["entity_type"] == "spec_rule"
    assert baseline.json()["snapshot"]["id"] == spec_a_id

    impact = client.post(
        "/api/v1/generation/impact",
        json={
            "old_expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 500},
                    {"level": "L2", "expected_nits": 800},
                ]
            },
            "new_expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 550},
                    {"level": "L2", "expected_nits": 800},
                ]
            },
            "existing_cases": mapping_cases,
        },
    )
    assert impact.status_code == 200
    assert len(impact.json()["impacted_case_ids"]) == 1

    history_ingest = client.post(
        "/api/v1/history/ingest",
        json={
            "cases": [
                {
                    "requirement_context": "backlight mapping",
                    "title": "Legacy backlight case",
                    "content": "Validate L1 maps to expected nits",
                    "metadata": {"source": "legacy"},
                }
            ]
        },
    )
    assert history_ingest.status_code == 200
    assert len(history_ingest.json()["inserted"]) == 1

    history_search = client.post(
        "/api/v1/history/search",
        json={"query": "backlight L1", "limit": 5},
    )
    assert history_search.status_code == 200
    assert len(history_search.json()["results"]) == 1

    arbitration = client.post(
        "/api/v1/generation/arbitration-combination",
        json={"spec_rule_ids": [spec_a_id, spec_b_id]},
    )
    assert arbitration.status_code == 200, arbitration.text
    arbitration_cases = arbitration.json()["cases"]
    assert any(
        case["case_type"] == "arbitration" and case["to_confirm"]
        for case in arbitration_cases
    )
    assert any(
        case["case_type"] == "combination" and not case["to_confirm"]
        for case in arbitration_cases
    )
