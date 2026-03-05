from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.knowledge.history import ingest_history_cases, retrieve_history_cases

router = APIRouter()


class HistoryCaseCreate(BaseModel):
    requirement_context: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class HistoryIngestRequest(BaseModel):
    cases: list[HistoryCaseCreate] = Field(min_length=1)


class HistorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = 5


@router.post("/ingest")
def ingest(payload: HistoryIngestRequest) -> dict:
    inserted = ingest_history_cases([item.model_dump() for item in payload.cases])
    return {"inserted": inserted}


@router.post("/search")
def search(payload: HistorySearchRequest) -> dict:
    return {"results": retrieve_history_cases(query=payload.query, limit=payload.limit)}
