from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.knowledge.workflow import create_baseline, transition_entity_state

router = APIRouter()


class TransitionRequest(BaseModel):
    to_state: str = Field(min_length=1)
    actor: str = Field(min_length=1)


class BaselineRequest(BaseModel):
    label: str = Field(min_length=1)
    actor: str = Field(min_length=1)


@router.post("/{entity_type}/{entity_id}/transition")
def transition(entity_type: str, entity_id: str, payload: TransitionRequest) -> dict:
    return transition_entity_state(
        entity_type=entity_type,
        entity_id=entity_id,
        to_state=payload.to_state,
        actor=payload.actor,
    )


@router.post("/{entity_type}/{entity_id}/baseline")
def baseline(entity_type: str, entity_id: str, payload: BaselineRequest) -> dict:
    return create_baseline(
        entity_type=entity_type,
        entity_id=entity_id,
        label=payload.label,
        actor=payload.actor,
    )
