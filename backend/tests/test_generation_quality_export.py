from io import BytesIO

from fastapi.testclient import TestClient
from helpers import create_reference, make_excel_bytes, upload_document
from openpyxl import load_workbook

from app.generation.actions import assert_relative, enter_menu, read_calibration, set_level, wait_ms
from app.main import app


def test_action_library_serializable() -> None:
    actions = [
        enter_menu("Display/Backlight"),
        set_level("L1"),
        wait_ms(500),
        read_calibration("nits"),
        assert_relative(expected_value=500, tolerance_percent=2, expected_source="spec_rule"),
    ]
    serialized = [item.to_dict() for item in actions]
    assert serialized[0]["kind"] == "EnterMenu"
    assert serialized[-1]["kind"] == "AssertRelative"
    assert serialized[-1]["params"]["expected_source"] == "spec_rule"


def test_mapping_generation_quality_and_export() -> None:
    client = TestClient(app)
    doc_id = upload_document(
        client,
        doc_key="gen-spec",
        version="v1",
        filename="mapping.xlsx",
        payload=make_excel_bytes(),
    )
    ref_id = create_reference(
        client,
        doc_id=doc_id,
        location="sheet:Backlight!A2",
        excerpt="L1 -> 500",
    )
    spec_rule = client.post(
        "/api/v1/knowledge/spec-rules",
        json={
            "name": "mapping rule",
            "rule_type": "mapping",
            "expression": {
                "mappings": [
                    {"level": "L1", "expected_nits": 500, "expected_source": "spec_rule"},
                    {"level": "L2", "expected_nits": 800, "expected_source": "spec_rule"},
                ]
            },
            "reference_ids": [ref_id],
        },
    )
    assert spec_rule.status_code == 200, spec_rule.text
    spec_rule_id = spec_rule.json()["id"]

    generated = client.post(f"/api/v1/generation/spec-rules/{spec_rule_id}/mapping-cases")
    assert generated.status_code == 200, generated.text
    body = generated.json()
    assert body["quality_report"]["passed"] is True
    assert len(body["cases"]) == 2

    first_case = body["cases"][0]
    assert first_case["expected"]["settle_time_ms"] == 500
    assert first_case["expected"]["tolerance_percent"] == 2.0
    step_kinds = [step["kind"] for step in first_case["steps"]]
    assert "ReadCal" in step_kinds
    assert "AssertRelative" in step_kinds

    quality = client.post(
        "/api/v1/quality/validate",
        json={"case_ids": [case["id"] for case in body["cases"]]},
    )
    assert quality.status_code == 200, quality.text
    assert quality.json()["passed"] is True

    exported = client.post(
        "/api/v1/export/test-cases.xlsx",
        json={"case_ids": [case["id"] for case in body["cases"]]},
    )
    assert exported.status_code == 200, exported.text
    workbook = load_workbook(BytesIO(exported.content))
    header = [cell.value for cell in workbook.active[1]]
    assert "reference_ids" in header
