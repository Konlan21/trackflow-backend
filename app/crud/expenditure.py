"""Mirrors tracker/views.py -> ExpenditureViewSet (scoped to request.user)."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expenditure import Expenditure
from app.schemas.expenditure import ExpenditureCreate, ExpenditureUpdate


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Expenditure]:
    result = await db.execute(
        select(Expenditure).where(Expenditure.user_id == user_id).order_by(Expenditure.created_at.desc())
    )
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, expenditure_id: uuid.UUID) -> Expenditure | None:
    result = await db.execute(
        select(Expenditure).where(Expenditure.id == expenditure_id, Expenditure.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: uuid.UUID, data: ExpenditureCreate) -> Expenditure:
    expenditure = Expenditure(
        user_id=user_id,
        category=data.category,
        nameOfItem=data.nameOfItem,
        amount=Decimal(data.amount),
    )
    db.add(expenditure)
    await db.commit()
    await db.refresh(expenditure)
    return expenditure


async def update(db: AsyncSession, expenditure: Expenditure, data: ExpenditureUpdate) -> Expenditure:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expenditure, field, value)
    await db.commit()
    await db.refresh(expenditure)
    return expenditure


async def delete(db: AsyncSession, expenditure: Expenditure) -> None:
    await db.delete(expenditure)
    await db.commit()