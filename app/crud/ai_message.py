"""Mirrors app/crud/goal.py conventions."""
import uuid

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_message import AIMessage, MessageRole


async def list_for_user(db: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> list[AIMessage]:
    result = await db.execute(
        select(AIMessage).where(AIMessage.user_id == user_id).order_by(AIMessage.created_at.asc()).limit(limit)
    )
    return list(result.scalars().all())


async def recent_for_context(db: AsyncSession, user_id: uuid.UUID, limit: int = 10) -> list[AIMessage]:
    """Last N messages, oldest first, for feeding back into the model as conversation context."""
    result = await db.execute(
        select(AIMessage).where(AIMessage.user_id == user_id).order_by(AIMessage.created_at.desc()).limit(limit)
    )
    rows = list(result.scalars().all())
    return list(reversed(rows))


async def add_message(db: AsyncSession, user_id: uuid.UUID, role: MessageRole, content: str) -> AIMessage:
    msg = AIMessage(user_id=user_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def clear_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(sa_delete(AIMessage).where(AIMessage.user_id == user_id))
    await db.commit()