"""Mirrors app/schemas/budget.py conventions."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.goal import GoalStatus


class GoalBase(BaseModel):
    title: str
    target_amount: Decimal = Field(ge=1)
    current_amount: Decimal = Field(default=0, ge=0)
    deadline: date | None = None
    status: GoalStatus = GoalStatus.IN_PROGRESS


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: str | None = None
    target_amount: Decimal | None = Field(default=None, ge=1)
    current_amount: Decimal | None = Field(default=None, ge=0)
    deadline: date | None = None
    status: GoalStatus | None = None


class GoalRead(GoalBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}