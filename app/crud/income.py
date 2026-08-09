"""Mirrors tracker/views.py -> IncomeViewSet (scoped to request.user)."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Income]:
    result = await db.execute(
        select(Income).where(Income.user_id == user_id).order_by(Income.created_at.desc())
    )
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, income_id: uuid.UUID) -> Income | None:
    result = await db.execute(
        select(Income).where(Income.id == income_id, Income.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: uuid.UUID, data: IncomeCreate) -> Income:
    income = Income(user_id=user_id, nameOfRevenue=data.nameOfRevenue, amount=Decimal(data.amount))
    db.add(income)
    await db.commit()
    await db.refresh(income)
    return income


async def update(db: AsyncSession, income: Income, data: IncomeUpdate) -> Income:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(income, field, value)
    await db.commit()
    await db.refresh(income)
    return income


async def delete(db: AsyncSession, income: Income) -> None:
    await db.delete(income)
    await db.commit()