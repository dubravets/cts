from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import get_connection
from app.quality.gates import validate_test_cases

router = APIRouter()


class ValidateRequest(BaseModel):
    case_ids: list[UUID]


@router.post("/validate")
def validate_cases(payload: ValidateRequest) -> dict:
    if not payload.case_ids:
        raise HTTPException(status_code=422, detail="case_ids cannot be empty")

    placeholders = ",".join("?" for _ in payload.case_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                id,
                name,
                case_type,
                source_spec_rule_id,
                to_confirm,
                status,
                steps_json,
                expected_json
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
                SELECT reference_id FROM test_case_references
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
                    "status": row["status"],
                    "to_confirm": bool(row["to_confirm"]),
                    "steps": json.loads(row["steps_json"]),
                    "expected": json.loads(row["expected_json"]),
                    "reference_ids": [item["reference_id"] for item in refs],
                }
            )

    report = validate_test_cases(cases).as_dict()
    if not report["passed"]:
        raise HTTPException(status_code=422, detail=report)
    return report
