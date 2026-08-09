"""Mirrors app/schemas/expenditure.py conventions, plus a summary schema."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.expenditure import ExpenditureCategory


class BudgetBase(BaseModel):
    category: ExpenditureCategory = ExpenditureCategory.OTHER
    monthly_limit: Decimal = Field(ge=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category: ExpenditureCategory | None = None
    monthly_limit: Decimal | None = Field(default=None, ge=0)
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=2000)


class BudgetRead(BudgetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetSummaryItem(BaseModel):
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percentage: float