from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from app.core.db import get_connection


def create_requirement(*, statement: str, reference_ids: list[str]) -> dict:
    _validate_reference_ids(reference_ids)
    requirement_id = str(uuid4())
    with get_connection() as conn:
        _ensure_references_exist(conn, reference_ids)
        conn.execute(
            """
            INSERT INTO requirements (id, statement, status)
            VALUES (?, ?, 'Draft')
            """,
            (requirement_id, statement),
        )
        for ref_id in reference_ids:
            conn.execute(
                """
                INSERT INTO requirement_references (requirement_id, reference_id)
                VALUES (?, ?)
                """,
                (requirement_id, ref_id),
            )
    return get_requirement(requirement_id)


def get_requirement(requirement_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, statement, status, created_at, updated_at
            FROM requirements
            WHERE id = ?
            """,
            (requirement_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Requirement not found")
        refs = conn.execute(
            """
            SELECT reference_id FROM requirement_references
            WHERE requirement_id = ?
            ORDER BY reference_id
            """,
            (requirement_id,),
        ).fetchall()
    return {
        "id": row["id"],
        "statement": row["statement"],
        "status": row["status"],
        "reference_ids": [item["reference_id"] for item in refs],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_requirement(
    *, requirement_id: str, statement: str, reference_ids: list[str]
) -> dict:
    _validate_reference_ids(reference_ids)
    with get_connection() as conn:
        _ensure_references_exist(conn, reference_ids)
        updated_at = datetime.now(UTC).isoformat()
        updated = conn.execute(
            """
            UPDATE requirements
            SET statement = ?, updated_at = ?
            WHERE id = ?
            """,
            (statement, updated_at, requirement_id),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="Requirement not found")
        conn.execute(
            "DELETE FROM requirement_references WHERE requirement_id = ?",
            (requirement_id,),
        )
        for ref_id in reference_ids:
            conn.execute(
                """
                INSERT INTO requirement_references (requirement_id, reference_id)
                VALUES (?, ?)
                """,
                (requirement_id, ref_id),
            )
    return get_requirement(requirement_id)


def delete_requirement(requirement_id: str) -> None:
    with get_connection() as conn:
        deleted = conn.execute("DELETE FROM requirements WHERE id = ?", (requirement_id,))
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="Requirement not found")


def create_spec_rule(
    *,
    name: str,
    rule_type: str,
    expression: dict,
    reference_ids: list[str],
) -> dict:
    _validate_reference_ids(reference_ids)
    spec_rule_id = str(uuid4())
    with get_connection() as conn:
        _ensure_references_exist(conn, reference_ids)
        conn.execute(
            """
            INSERT INTO spec_rules (id, name, rule_type, expression_json, status)
            VALUES (?, ?, ?, ?, 'Draft')
            """,
            (spec_rule_id, name, rule_type, json.dumps(expression, sort_keys=True)),
        )
        for ref_id in reference_ids:
            conn.execute(
                """
                INSERT INTO spec_rule_references (spec_rule_id, reference_id)
                VALUES (?, ?)
                """,
                (spec_rule_id, ref_id),
            )
    return get_spec_rule(spec_rule_id)


def get_spec_rule(spec_rule_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, rule_type, expression_json, status, created_at, updated_at
            FROM spec_rules
            WHERE id = ?
            """,
            (spec_rule_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="SpecRule not found")
        refs = conn.execute(
            """
            SELECT reference_id FROM spec_rule_references
            WHERE spec_rule_id = ?
            ORDER BY reference_id
            """,
            (spec_rule_id,),
        ).fetchall()
    return {
        "id": row["id"],
        "name": row["name"],
        "rule_type": row["rule_type"],
        "expression": json.loads(row["expression_json"]),
        "status": row["status"],
        "reference_ids": [item["reference_id"] for item in refs],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_spec_rule(
    *,
    spec_rule_id: str,
    name: str,
    rule_type: str,
    expression: dict,
    reference_ids: list[str],
) -> dict:
    _validate_reference_ids(reference_ids)
    with get_connection() as conn:
        _ensure_references_exist(conn, reference_ids)
        updated_at = datetime.now(UTC).isoformat()
        updated = conn.execute(
            """
            UPDATE spec_rules
            SET name = ?, rule_type = ?, expression_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, rule_type, json.dumps(expression, sort_keys=True), updated_at, spec_rule_id),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="SpecRule not found")
        conn.execute(
            "DELETE FROM spec_rule_references WHERE spec_rule_id = ?",
            (spec_rule_id,),
        )
        for ref_id in reference_ids:
            conn.execute(
                """
                INSERT INTO spec_rule_references (spec_rule_id, reference_id)
                VALUES (?, ?)
                """,
                (spec_rule_id, ref_id),
            )
    return get_spec_rule(spec_rule_id)


def delete_spec_rule(spec_rule_id: str) -> None:
    with get_connection() as conn:
        deleted = conn.execute("DELETE FROM spec_rules WHERE id = ?", (spec_rule_id,))
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="SpecRule not found")


def list_spec_rules() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM spec_rules ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [get_spec_rule(row["id"]) for row in rows]


def _validate_reference_ids(reference_ids: list[str]) -> None:
    if not reference_ids:
        raise HTTPException(
            status_code=422, detail="At least one reference_id is required for traceability"
        )


def _ensure_references_exist(conn, reference_ids: list[str]) -> None:
    placeholders = ",".join("?" for _ in reference_ids)
    rows = conn.execute(
        f'SELECT id FROM "references" WHERE id IN ({placeholders})',
        tuple(reference_ids),
    ).fetchall()
    found = {row["id"] for row in rows}
    missing = sorted(set(reference_ids) - found)
    if missing:
        raise HTTPException(status_code=404, detail=f"Reference not found: {missing[0]}")
