from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from app.core.db import get_connection
from app.knowledge.store import get_requirement, get_spec_rule

ALLOWED_STATES = {"Draft", "Review", "Published"}
ENTITY_TABLES = {
    "requirement": "requirements",
    "spec_rule": "spec_rules",
    "test_case": "test_cases",
}


def transition_entity_state(
    *, entity_type: str, entity_id: str, to_state: str, actor: str
) -> dict:
    if to_state not in ALLOWED_STATES:
        raise HTTPException(status_code=422, detail=f"Unsupported workflow state: {to_state}")

    table = ENTITY_TABLES.get(entity_type)
    if table is None:
        raise HTTPException(status_code=422, detail=f"Unsupported entity_type: {entity_type}")

    updated_at = datetime.now(UTC).isoformat()
    with get_connection() as conn:
        updated = conn.execute(
            f"UPDATE {table} SET status = ?, updated_at = ? WHERE id = ?",
            (to_state, updated_at, entity_id),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"{entity_type} not found")
    return {"entity_type": entity_type, "entity_id": entity_id, "state": to_state, "actor": actor}


def create_baseline(*, entity_type: str, entity_id: str, label: str, actor: str) -> dict:
    snapshot = _load_entity_snapshot(entity_type=entity_type, entity_id=entity_id)
    baseline_id = str(uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO baselines (id, entity_type, entity_id, label, snapshot_json, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                baseline_id,
                entity_type,
                entity_id,
                label,
                json.dumps(snapshot, sort_keys=True),
                actor,
            ),
        )
        row = conn.execute(
            """
            SELECT id, entity_type, entity_id, label, snapshot_json, created_by, created_at
            FROM baselines WHERE id = ?
            """,
            (baseline_id,),
        ).fetchone()
    return {
        "id": row["id"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "label": row["label"],
        "snapshot": json.loads(row["snapshot_json"]),
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


def _load_entity_snapshot(*, entity_type: str, entity_id: str) -> dict:
    if entity_type == "requirement":
        return get_requirement(entity_id)
    if entity_type == "spec_rule":
        return get_spec_rule(entity_id)
    if entity_type == "test_case":
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, case_type, status, to_confirm, steps_json, expected_json
                FROM test_cases WHERE id = ?
                """,
                (entity_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="test_case not found")
            refs = conn.execute(
                """
                SELECT reference_id FROM test_case_references
                WHERE test_case_id = ?
                ORDER BY reference_id
                """,
                (entity_id,),
            ).fetchall()
        return {
            "id": row["id"],
            "name": row["name"],
            "case_type": row["case_type"],
            "status": row["status"],
            "to_confirm": bool(row["to_confirm"]),
            "steps_json": row["steps_json"],
            "expected_json": row["expected_json"],
            "reference_ids": [item["reference_id"] for item in refs],
        }

    raise HTTPException(status_code=422, detail=f"Unsupported entity_type: {entity_type}")
