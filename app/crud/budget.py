"""Mirrors app/crud/expenditure.py conventions."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Budget]:
    result = await db.execute(
        select(Budget).where(Budget.user_id == user_id).order_by(Budget.year.desc(), Budget.month.desc())
    )
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget | None:
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
    budget = Budget(
        user_id=user_id,
        category=data.category,
        monthly_limit=Decimal(data.monthly_limit),
        month=data.month,
        year=data.year,
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


async def update(db: AsyncSession, budget: Budget, data: BudgetUpdate) -> Budget:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    await db.commit()
    await db.refresh(budget)
    return budget


async def delete(db: AsyncSession, budget: Budget) -> None:
    await db.delete(budget)
    await db.commit()