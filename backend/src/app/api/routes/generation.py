from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db import get_connection
from app.generation.arbitration import generate_arbitration_and_combination_cases
from app.generation.engine import (
    GeneratedCase,
    generate_mapping_cases,
    generate_threshold_cases,
)
from app.generation.extensions import generate_invalid_cases
from app.generation.impact import impacted_cases_from_mapping_diff
from app.knowledge.store import get_spec_rule
from app.quality.gates import validate_test_cases

router = APIRouter()


class GenerateResult(BaseModel):
    cases: list[dict]
    quality_report: dict


class ArbitrationRequest(BaseModel):
    spec_rule_ids: list[UUID] = Field(min_length=2)


class ImpactRequest(BaseModel):
    old_expression: dict
    new_expression: dict
    existing_cases: list[dict]


@router.post("/spec-rules/{spec_rule_id}/mapping-cases", response_model=GenerateResult)
def generate_mapping_cases_endpoint(spec_rule_id: UUID) -> GenerateResult:
    spec_rule = get_spec_rule(str(spec_rule_id))
    generated = generate_mapping_cases(
        source_spec_rule_id=spec_rule["id"],
        source_spec_rule_name=spec_rule["name"],
        expression=spec_rule["expression"],
        reference_ids=spec_rule["reference_ids"],
        project_config=_load_project_config(),
    )
    return _persist_and_validate(generated)


@router.post("/spec-rules/{spec_rule_id}/threshold-cases", response_model=GenerateResult)
def generate_threshold_cases_endpoint(spec_rule_id: UUID) -> GenerateResult:
    spec_rule = get_spec_rule(str(spec_rule_id))
    generated = generate_threshold_cases(
        source_spec_rule_id=spec_rule["id"],
        source_spec_rule_name=spec_rule["name"],
        expression=spec_rule["expression"],
        reference_ids=spec_rule["reference_ids"],
        project_config=_load_project_config(),
    )
    return _persist_and_validate(generated)


@router.post("/spec-rules/{spec_rule_id}/invalid-cases", response_model=GenerateResult)
def generate_invalid_cases_endpoint(spec_rule_id: UUID) -> GenerateResult:
    spec_rule = get_spec_rule(str(spec_rule_id))
    generated = generate_invalid_cases(
        source_spec_rule_id=spec_rule["id"],
        source_spec_rule_name=spec_rule["name"],
        expression=spec_rule["expression"],
        reference_ids=spec_rule["reference_ids"],
    )
    return _persist_and_validate(generated)


@router.post("/arbitration-combination", response_model=GenerateResult)
def generate_arbitration_combination_endpoint(payload: ArbitrationRequest) -> GenerateResult:
    spec_rules = [get_spec_rule(str(item)) for item in payload.spec_rule_ids]
    all_refs = sorted({ref for spec in spec_rules for ref in spec["reference_ids"]})
    generated = generate_arbitration_and_combination_cases(
        spec_rules=spec_rules,
        reference_ids=all_refs,
        settle_time_ms=_load_project_config()["settle_time_ms"],
        tolerance_percent=_load_project_config()["tolerance_percent"],
    )
    return _persist_and_validate(generated)


@router.post("/impact")
def impact_endpoint(payload: ImpactRequest) -> dict:
    impacted = impacted_cases_from_mapping_diff(
        old_expression=payload.old_expression,
        new_expression=payload.new_expression,
        existing_cases=payload.existing_cases,
    )
    return {"impacted_case_ids": impacted}


def _persist_and_validate(generated: list[GeneratedCase]) -> GenerateResult:
    case_dicts = [
        {
            "id": case.id,
            "name": case.name,
            "case_type": case.case_type,
            "source_spec_rule_id": case.source_spec_rule_id,
            "status": case.status,
            "to_confirm": case.to_confirm,
            "steps": case.steps,
            "expected": case.expected,
            "reference_ids": case.reference_ids,
        }
        for case in generated
    ]
    quality_report = validate_test_cases(case_dicts).as_dict()
    if not quality_report["passed"]:
        raise HTTPException(status_code=422, detail=quality_report)

    with get_connection() as conn:
        for case in case_dicts:
            conn.execute(
                """
                INSERT OR REPLACE INTO test_cases (
                    id, name, case_type, source_spec_rule_id, to_confirm, status,
                    steps_json, expected_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case["id"],
                    case["name"],
                    case["case_type"],
                    case["source_spec_rule_id"],
                    int(case["to_confirm"]),
                    case["status"],
                    json.dumps(case["steps"], sort_keys=True),
                    json.dumps(case["expected"], sort_keys=True),
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.execute("DELETE FROM test_case_references WHERE test_case_id = ?", (case["id"],))
            for ref_id in case["reference_ids"]:
                conn.execute(
                    """
                    INSERT INTO test_case_references (test_case_id, reference_id)
                    VALUES (?, ?)
                    """,
                    (case["id"], ref_id),
                )

    return GenerateResult(cases=case_dicts, quality_report=quality_report)


def _load_project_config() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT settle_time_ms, tolerance_percent
            FROM project_config
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO project_config (id, settle_time_ms, tolerance_percent)
                VALUES (1, 500, 2.0)
                """
            )
            return {"settle_time_ms": 500, "tolerance_percent": 2.0}
    return {"settle_time_ms": row["settle_time_ms"], "tolerance_percent": row["tolerance_percent"]}
