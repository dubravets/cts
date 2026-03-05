from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db import get_connection

router = APIRouter()


class ReferenceCreate(BaseModel):
    doc_id: UUID
    location: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)


class ReferenceRead(ReferenceCreate):
    id: UUID
    created_at: datetime


@router.post("", response_model=ReferenceRead)
def create_reference(payload: ReferenceCreate) -> ReferenceRead:
    with get_connection() as conn:
        doc_exists = conn.execute(
            "SELECT 1 FROM documents WHERE id = ?",
            (str(payload.doc_id),),
        ).fetchone()
        if doc_exists is None:
            raise HTTPException(status_code=404, detail="Document not found")

        reference_id = uuid4()
        conn.execute(
            """
            INSERT INTO "references" (id, doc_id, location, excerpt)
            VALUES (?, ?, ?, ?)
            """,
            (str(reference_id), str(payload.doc_id), payload.location, payload.excerpt),
        )
        row = conn.execute(
            """
            SELECT id, doc_id, location, excerpt, created_at
            FROM "references"
            WHERE id = ?
            """,
            (str(reference_id),),
        ).fetchone()
    return _to_reference_read(row)


@router.get("/{reference_id}", response_model=ReferenceRead)
def get_reference(reference_id: UUID) -> ReferenceRead:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, doc_id, location, excerpt, created_at
            FROM "references"
            WHERE id = ?
            """,
            (str(reference_id),),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Reference not found")

    return _to_reference_read(row)


def _to_reference_read(row) -> ReferenceRead:
    return ReferenceRead(
        id=UUID(row["id"]),
        doc_id=UUID(row["doc_id"]),
        location=row["location"],
        excerpt=row["excerpt"],
        created_at=row["created_at"],
    )
