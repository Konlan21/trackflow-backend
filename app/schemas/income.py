"""Mirrors tracker/serializers.py -> IncomeSerializer."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class IncomeBase(BaseModel):
    nameOfRevenue: str
    amount: Decimal = Field(ge=1)


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    nameOfRevenue: str | None = None
    amount: Decimal | None = Field(default=None, ge=1)


class IncomeRead(IncomeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}