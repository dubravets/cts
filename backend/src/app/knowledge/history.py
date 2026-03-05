from __future__ import annotations

import json
from uuid import uuid4

from app.core.db import get_connection


def ingest_history_cases(cases: list[dict]) -> list[dict]:
    inserted: list[dict] = []
    with get_connection() as conn:
        for case in cases:
            case_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO history_cases (id, requirement_context, title, content, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    case["requirement_context"],
                    case["title"],
                    case["content"],
                    json.dumps(case.get("metadata", {}), sort_keys=True),
                ),
            )
            row = conn.execute(
                """
                SELECT id, requirement_context, title, content, metadata_json, created_at
                FROM history_cases WHERE id = ?
                """,
                (case_id,),
            ).fetchone()
            inserted.append(_row_to_history_case(row))
    return inserted


def retrieve_history_cases(*, query: str, limit: int = 5) -> list[dict]:
    query_tokens = {token for token in _tokenize(query) if token}
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, requirement_context, title, content, metadata_json, created_at
            FROM history_cases
            ORDER BY created_at DESC
            """
        ).fetchall()

    scored: list[tuple[int, dict]] = []
    for row in rows:
        case = _row_to_history_case(row)
        haystack = " ".join([case["requirement_context"], case["title"], case["content"]])
        tokens = set(_tokenize(haystack))
        score = len(query_tokens & tokens)
        if score > 0:
            scored.append((score, case))

    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [item[1] for item in scored[:limit]]


def _row_to_history_case(row) -> dict:
    return {
        "id": row["id"],
        "requirement_context": row["requirement_context"],
        "title": row["title"],
        "content": row["content"],
        "metadata": json.loads(row["metadata_json"]),
        "created_at": row["created_at"],
    }


def _tokenize(text: str) -> list[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in normalized.split() if token]
