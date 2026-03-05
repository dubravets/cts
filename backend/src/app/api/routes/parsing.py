from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import get_connection
from app.parsing.excel import parse_excel_file
from app.parsing.word import parse_word_file

router = APIRouter()


class ParseProfileCreate(BaseModel):
    name: str
    parser_type: str
    options: dict


class ParseProfileRead(BaseModel):
    id: UUID
    name: str
    parser_type: str
    options: dict
    created_at: datetime
    updated_at: datetime


def _row_to_parse_profile(row) -> ParseProfileRead:
    return ParseProfileRead(
        id=UUID(row["id"]),
        name=row["name"],
        parser_type=row["parser_type"],
        options=json.loads(row["options_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("/profiles", response_model=ParseProfileRead)
def create_parse_profile(payload: ParseProfileCreate) -> ParseProfileRead:
    if payload.parser_type not in {"excel", "word"}:
        raise HTTPException(status_code=422, detail="parser_type must be excel or word")

    profile_id = str(uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO parse_profiles (id, name, parser_type, options_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                payload.name,
                payload.parser_type,
                json.dumps(payload.options, sort_keys=True),
            ),
        )
        row = conn.execute(
            """
            SELECT id, name, parser_type, options_json, created_at, updated_at
            FROM parse_profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()
    return _row_to_parse_profile(row)


@router.get("/profiles/{profile_id}", response_model=ParseProfileRead)
def get_parse_profile(profile_id: UUID) -> ParseProfileRead:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, parser_type, options_json, created_at, updated_at
            FROM parse_profiles
            WHERE id = ?
            """,
            (str(profile_id),),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Parse profile not found")
    return _row_to_parse_profile(row)


@router.post("/profiles/{profile_id}/preview/{document_id}")
def preview_with_profile(profile_id: UUID, document_id: UUID) -> dict:
    with get_connection() as conn:
        profile = conn.execute(
            """
            SELECT id, name, parser_type, options_json
            FROM parse_profiles
            WHERE id = ?
            """,
            (str(profile_id),),
        ).fetchone()
        if profile is None:
            raise HTTPException(status_code=404, detail="Parse profile not found")

        document = conn.execute(
            """
            SELECT id, storage_path FROM documents WHERE id = ?
            """,
            (str(document_id),),
        ).fetchone()
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")

    storage_path = Path(document["storage_path"])
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Document file missing")

    parser_type = profile["parser_type"]
    if parser_type == "excel":
        rows = parse_excel_file(file_path=storage_path, doc_id=str(document_id))
        return {
            "parser_type": "excel",
            "rows": [
                {
                    "sheet_name": row.sheet_name,
                    "row_index": row.row_index,
                    "reference": {
                        "doc_id": row.reference.doc_id,
                        "location": row.reference.location,
                        "excerpt": row.reference.excerpt,
                    },
                    "cells": [
                        {
                            "coordinate": cell.coordinate,
                            "source_coordinate": cell.source_coordinate,
                            "value": cell.value,
                        }
                        for cell in row.cells
                    ],
                }
                for row in rows
            ],
        }

    if parser_type == "word":
        result = parse_word_file(file_path=storage_path, doc_id=str(document_id))
        return {
            "parser_type": "word",
            "heading_paths": result.heading_paths,
            "mapping_candidates": [
                {
                    "heading_path": item.heading_path,
                    "level": item.level,
                    "expected_value_text": item.expected_value_text,
                    "reference": {
                        "doc_id": item.reference.doc_id,
                        "location": item.reference.location,
                        "excerpt": item.reference.excerpt,
                    },
                }
                for item in result.mapping_candidates
            ],
        }

    raise HTTPException(status_code=422, detail="Unsupported parser_type")
