from __future__ import annotations

import json
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.db import get_connection
from app.export.xlsx_export import export_test_cases_to_xlsx

router = APIRouter()


class ExportRequest(BaseModel):
    case_ids: list[UUID]


@router.post("/test-cases.xlsx")
def export_test_cases(payload: ExportRequest) -> StreamingResponse:
    if not payload.case_ids:
        raise HTTPException(status_code=422, detail="case_ids cannot be empty")

    placeholders = ",".join("?" for _ in payload.case_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, name, case_type, source_spec_rule_id, steps_json, expected_json
            FROM test_cases
            WHERE id IN ({placeholders})
            ORDER BY id
            """,
            tuple(str(item) for item in payload.case_ids),
        ).fetchall()
        cases: list[dict] = []
        for row in rows:
            refs = conn.execute(
                """
                SELECT reference_id
                FROM test_case_references
                WHERE test_case_id = ?
                ORDER BY reference_id
                """,
                (row["id"],),
            ).fetchall()
            cases.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "case_type": row["case_type"],
                    "source_spec_rule_id": row["source_spec_rule_id"],
                    "steps": json.loads(row["steps_json"]),
                    "expected": json.loads(row["expected_json"]),
                    "reference_ids": [item["reference_id"] for item in refs],
                }
            )

    data = export_test_cases_to_xlsx(cases)
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="test_cases.xlsx"'},
    )
