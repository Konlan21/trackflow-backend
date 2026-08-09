"""
Expanded AI endpoints (Phase 9):
  POST   /user/ai/chat      -> chat with financial context + history, persists both turns
  GET    /user/ai/history   -> full chat history
  DELETE /user/ai/history   -> clear chat history

Reuses the same Gemini call pattern as tracker.py's ai-query endpoint,
but adds budgets/goals to the context and keeps a running conversation.
"""
import asyncio
import os
import time
from decimal import Decimal
from app.core.config import settings

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import ai_message as ai_message_crud
from app.db.session import get_db
from app.models.budget import Budget
from app.models.expenditure import Expenditure
from app.models.goal import Goal
from app.models.income import Income
from app.models.ai_message import MessageRole
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse, AIMessageRead

router = APIRouter(prefix="/ai", tags=["ai"])


def _generate_ai_reply_sync(
    user_message: str,
    total_income: Decimal,
    total_expense: Decimal,
    recent_expenses: list[dict],
    budgets: list[dict],
    goals: list[dict],
    history: list[dict],
) -> str:
    net_balance = total_income - total_expense

    system_instruction = (
        "You are TrackFlow AI, an intelligent personal finance assistant. "
        "Use the user's financial data (income, expenses, budgets, goals) to answer clearly. "
        "Keep responses concise, actionable, and under 4 sentences unless asked for detail."
    )
    context = (
        f"Financial Summary:\n"
        f"- Total Income: ${total_income:.2f}\n"
        f"- Total Expenses: ${total_expense:.2f}\n"
        f"- Net Balance: ${net_balance:.2f}\n"
        f"- Recent Expenses: {recent_expenses}\n"
        f"- Budgets: {budgets}\n"
        f"- Goals: {goals}\n"
    )

    api_key = settings.GEMINI_API_KEY
    fallback = (
        f"Current Balance: ${net_balance:.2f} (Income: ${total_income:.2f}, "
        f"Expenses: ${total_expense:.2f}). Keep tracking to unlock full AI insights!"
    )
    if not api_key:
        return fallback

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Build multi-turn contents: prior turns + new user message
    contents = []
    for turn in history:
        contents.append({"role": turn["role"], "parts": [{"text": turn["content"]}]})
    contents.append({"role": "user", "parts": [{"text": f"{context}\n\nUser: {user_message}"}]})

    max_retries = 3
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7),
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            break

    return fallback


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(data: AIChatRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    total_income = (
        await db.execute(select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == user_id))
    ).scalar_one()
    total_expense = (
        await db.execute(select(func.coalesce(func.sum(Expenditure.amount), 0)).where(Expenditure.user_id == user_id))
    ).scalar_one()
    recent = (
        await db.execute(
            select(Expenditure.nameOfItem, Expenditure.amount, Expenditure.category)
            .where(Expenditure.user_id == user_id)
            .order_by(Expenditure.created_at.desc())
            .limit(5)
        )
    ).all()
    recent_expenses = [{"nameOfItem": r[0], "amount": float(r[1]), "category": r[2].value} for r in recent]

    budget_rows = (await db.execute(select(Budget).where(Budget.user_id == user_id))).scalars().all()
    budgets = [
        {"category": b.category.value, "monthly_limit": float(b.monthly_limit), "month": b.month, "year": b.year}
        for b in budget_rows
    ]

    goal_rows = (await db.execute(select(Goal).where(Goal.user_id == user_id))).scalars().all()
    goals = [
        {
            "title": g.title,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "status": g.status.value,
        }
        for g in goal_rows
    ]

    history_rows = await ai_message_crud.recent_for_context(db, user_id, limit=10)
    history = [
        {"role": "user" if h.role == MessageRole.USER else "model", "content": h.content} for h in history_rows
    ]

    reply = await asyncio.to_thread(
        _generate_ai_reply_sync,
        data.message,
        Decimal(total_income),
        Decimal(total_expense),
        recent_expenses,
        budgets,
        goals,
        history,
    )

    await ai_message_crud.add_message(db, user_id, MessageRole.USER, data.message)
    await ai_message_crud.add_message(db, user_id, MessageRole.ASSISTANT, reply)

    return AIChatResponse(reply=reply)


@router.get("/history", response_model=list[AIMessageRead])
async def ai_history(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ai_message_crud.list_for_user(db, current_user.id)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_ai_history(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await ai_message_crud.clear_for_user(db, current_user.id)