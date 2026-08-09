"""Mirrors tracker/serializers.py -> ExpenditureSerializer."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.expenditure import ExpenditureCategory


class ExpenditureBase(BaseModel):
    category: ExpenditureCategory = ExpenditureCategory.OTHER
    nameOfItem: str
    amount: Decimal = Field(ge=1)


class ExpenditureCreate(ExpenditureBase):
    pass


class ExpenditureUpdate(BaseModel):
    category: ExpenditureCategory | None = None
    nameOfItem: str | None = None
    amount: Decimal | None = Field(default=None, ge=1)


class ExpenditureRead(ExpenditureBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}