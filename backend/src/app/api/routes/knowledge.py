from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.knowledge.store import (
    create_requirement,
    create_spec_rule,
    delete_requirement,
    delete_spec_rule,
    get_requirement,
    get_spec_rule,
    list_spec_rules,
    update_requirement,
    update_spec_rule,
)

router = APIRouter()


class RequirementCreate(BaseModel):
    statement: str = Field(min_length=1)
    reference_ids: list[UUID] = Field(min_length=1)


class RequirementRead(BaseModel):
    id: UUID
    statement: str
    status: str
    reference_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class SpecRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    rule_type: str = Field(min_length=1)
    expression: dict
    reference_ids: list[UUID] = Field(min_length=1)


class SpecRuleRead(BaseModel):
    id: UUID
    name: str
    rule_type: str
    expression: dict
    status: str
    reference_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


@router.post("/requirements", response_model=RequirementRead)
def create_requirement_endpoint(payload: RequirementCreate) -> RequirementRead:
    row = create_requirement(
        statement=payload.statement,
        reference_ids=[str(item) for item in payload.reference_ids],
    )
    return RequirementRead(**row)


@router.get("/requirements/{requirement_id}", response_model=RequirementRead)
def get_requirement_endpoint(requirement_id: UUID) -> RequirementRead:
    return RequirementRead(**get_requirement(str(requirement_id)))


@router.put("/requirements/{requirement_id}", response_model=RequirementRead)
def update_requirement_endpoint(
    requirement_id: UUID, payload: RequirementCreate
) -> RequirementRead:
    row = update_requirement(
        requirement_id=str(requirement_id),
        statement=payload.statement,
        reference_ids=[str(item) for item in payload.reference_ids],
    )
    return RequirementRead(**row)


@router.delete("/requirements/{requirement_id}")
def delete_requirement_endpoint(requirement_id: UUID) -> dict:
    delete_requirement(str(requirement_id))
    return {"deleted": str(requirement_id)}


@router.post("/spec-rules", response_model=SpecRuleRead)
def create_spec_rule_endpoint(payload: SpecRuleCreate) -> SpecRuleRead:
    row = create_spec_rule(
        name=payload.name,
        rule_type=payload.rule_type,
        expression=payload.expression,
        reference_ids=[str(item) for item in payload.reference_ids],
    )
    return SpecRuleRead(**row)


@router.get("/spec-rules/{spec_rule_id}", response_model=SpecRuleRead)
def get_spec_rule_endpoint(spec_rule_id: UUID) -> SpecRuleRead:
    return SpecRuleRead(**get_spec_rule(str(spec_rule_id)))


@router.put("/spec-rules/{spec_rule_id}", response_model=SpecRuleRead)
def update_spec_rule_endpoint(spec_rule_id: UUID, payload: SpecRuleCreate) -> SpecRuleRead:
    row = update_spec_rule(
        spec_rule_id=str(spec_rule_id),
        name=payload.name,
        rule_type=payload.rule_type,
        expression=payload.expression,
        reference_ids=[str(item) for item in payload.reference_ids],
    )
    return SpecRuleRead(**row)


@router.delete("/spec-rules/{spec_rule_id}")
def delete_spec_rule_endpoint(spec_rule_id: UUID) -> dict:
    delete_spec_rule(str(spec_rule_id))
    return {"deleted": str(spec_rule_id)}


@router.get("/spec-rules", response_model=list[SpecRuleRead])
def list_spec_rules_endpoint() -> list[SpecRuleRead]:
    return [SpecRuleRead(**item) for item in list_spec_rules()]
