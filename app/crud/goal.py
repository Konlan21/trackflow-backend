"""Mirrors app/crud/budget.py conventions."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalStatus
from app.schemas.goal import GoalCreate, GoalUpdate


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Goal]:
    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    )
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal | None:
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: uuid.UUID, data: GoalCreate) -> Goal:
    goal = Goal(
        user_id=user_id,
        title=data.title,
        target_amount=Decimal(data.target_amount),
        current_amount=Decimal(data.current_amount),
        deadline=data.deadline,
        status=data.status,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def update(db: AsyncSession, goal: Goal, data: GoalUpdate) -> Goal:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)

    # auto-complete when current_amount reaches target_amount, unless caller
    # explicitly set a different status in this same request
    if "status" not in data.model_dump(exclude_unset=True) and goal.current_amount >= goal.target_amount:
        goal.status = GoalStatus.COMPLETED

    await db.commit()
    await db.refresh(goal)
    return goal


async def delete(db: AsyncSession, goal: Goal) -> None:
    await db.delete(goal)
    await db.commit()