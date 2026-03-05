from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

TRACEABILITY_HEADERS = [
    "case_id",
    "name",
    "case_type",
    "source_spec_rule_id",
    "level",
    "expected_source",
    "settle_time_ms",
    "tolerance_percent",
    "reference_ids",
    "steps_json",
]


def export_test_cases_to_xlsx(cases: list[dict]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "TestCases"
    worksheet.append(TRACEABILITY_HEADERS)

    for case in cases:
        expected = case.get("expected", {})
        worksheet.append(
            [
                case.get("id"),
                case.get("name"),
                case.get("case_type"),
                case.get("source_spec_rule_id"),
                expected.get("level"),
                expected.get("expected_source"),
                expected.get("settle_time_ms"),
                expected.get("tolerance_percent"),
                ",".join(case.get("reference_ids", [])),
                str(case.get("steps", [])),
            ]
        )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
