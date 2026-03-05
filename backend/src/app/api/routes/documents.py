from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copyfileobj
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.db import get_connection, get_data_dir

router = APIRouter()


class DocumentRead(BaseModel):
    id: UUID
    doc_key: str
    version: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


def _safe_segment(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)


def _uploads_dir() -> Path:
    path = get_data_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _row_to_document(row: sqlite3.Row) -> DocumentRead:
    return DocumentRead(
        id=UUID(row["id"]),
        doc_key=row["doc_key"],
        version=row["version"],
        filename=row["filename"],
        content_type=row["content_type"],
        size_bytes=row["size_bytes"],
        created_at=row["created_at"],
    )


@router.post("", response_model=DocumentRead)
def upload_document(
    doc_key: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
) -> DocumentRead:
    clean_doc_key = doc_key.strip()
    clean_version = version.strip()
    if not clean_doc_key or not clean_version:
        raise HTTPException(status_code=422, detail="doc_key and version are required")

    if not file.filename:
        raise HTTPException(status_code=422, detail="file name is required")

    doc_id = uuid4()
    safe_name = _safe_segment(file.filename)
    target_dir = _uploads_dir() / _safe_segment(clean_doc_key)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{_safe_segment(clean_version)}_{doc_id}_{safe_name}"

    with target_path.open("wb") as out:
        copyfileobj(file.file, out)
    size_bytes = target_path.stat().st_size

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    id, doc_key, version, filename, content_type, size_bytes, storage_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(doc_id),
                    clean_doc_key,
                    clean_version,
                    file.filename,
                    file.content_type or "application/octet-stream",
                    size_bytes,
                    str(target_path),
                ),
            )
            row = conn.execute(
                """
                SELECT id, doc_key, version, filename, content_type, size_bytes, created_at
                FROM documents
                WHERE id = ?
                """,
                (str(doc_id),),
            ).fetchone()
    except sqlite3.IntegrityError:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409, detail=f"Version already exists for doc_key '{clean_doc_key}'"
        ) from None

    return _row_to_document(row)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID) -> DocumentRead:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, doc_key, version, filename, content_type, size_bytes, created_at
            FROM documents
            WHERE id = ?
            """,
            (str(document_id),),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _row_to_document(row)


@router.get("/{doc_key}/versions", response_model=list[DocumentRead])
def list_document_versions(doc_key: str) -> list[DocumentRead]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, doc_key, version, filename, content_type, size_bytes, created_at
            FROM documents
            WHERE doc_key = ?
            ORDER BY created_at DESC
            """,
            (doc_key,),
        ).fetchall()
    return [_row_to_document(row) for row in rows]
