from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import get_connection

router = APIRouter()


class ReferenceCreate(BaseModel):
    doc_id: str
    location: str
    excerpt: str


class ReferenceRead(ReferenceCreate):
    id: UUID


@router.post("", response_model=ReferenceRead)
def create_reference(payload: ReferenceCreate) -> ReferenceRead:
    ref = ReferenceRead(id=uuid4(), **payload.model_dump())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO "references" (id, doc_id, location, excerpt)
            VALUES (?, ?, ?, ?)
            """,
            (str(ref.id), ref.doc_id, ref.location, ref.excerpt),
        )
    return ref


@router.get("/{reference_id}", response_model=ReferenceRead)
def get_reference(reference_id: UUID) -> ReferenceRead:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, doc_id, location, excerpt
            FROM "references"
            WHERE id = ?
            """,
            (str(reference_id),),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Reference not found")

    return ReferenceRead(
        id=UUID(row["id"]),
        doc_id=row["doc_id"],
        location=row["location"],
        excerpt=row["excerpt"],
    )
