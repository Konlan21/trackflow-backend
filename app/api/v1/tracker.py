"""
Mirrors tracker/urls.py + tracker/views.py:
  /user/income          (list, create)
  /user/income/{id}     (retrieve, update, patch, delete)
  /user/expenditure      (list, create)
  /user/expenditure/{id} (retrieve, update, patch, delete)
  /user/ai-query/
  /user/dashboard/
"""
import asyncio
import os
import time
import uuid
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import expenditure as expenditure_crud
from app.crud import income as income_crud
from app.db.session import get_db
from app.models.expenditure import Expenditure
from app.models.income import Income
from app.models.user import User
from app.schemas.dashboard import AIQueryRequest, AIQueryResponse, DashboardResponse
from app.schemas.expenditure import ExpenditureCreate, ExpenditureRead, ExpenditureUpdate
from app.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate

router = APIRouter()


# --------------------------------------------------------------------------
# Income
# --------------------------------------------------------------------------
income_router = APIRouter(prefix="/income", tags=["income"])


@income_router.get("", response_model=list[IncomeRead])
async def list_incomes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await income_crud.list_for_user(db, current_user.id)


@income_router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
async def create_income(data: IncomeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await income_crud.create(db, current_user.id, data)


@income_router.get("/{incomeID}", response_model=IncomeRead)
async def retrieve_income(incomeID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = await income_crud.get_for_user(db, current_user.id, incomeID)
    if income is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return income


@income_router.put("/{incomeID}", response_model=IncomeRead)
@income_router.patch("/{incomeID}", response_model=IncomeRead)
async def update_income(
    incomeID: uuid.UUID,
    data: IncomeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income = await income_crud.get_for_user(db, current_user.id, incomeID)
    if income is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return await income_crud.update(db, income, data)


@income_router.delete("/{incomeID}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(incomeID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = await income_crud.get_for_user(db, current_user.id, incomeID)
    if income is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    await income_crud.delete(db, income)


# --------------------------------------------------------------------------
# Expenditure
# --------------------------------------------------------------------------
expenditure_router = APIRouter(prefix="/expenditure", tags=["expenditure"])


@expenditure_router.get("", response_model=list[ExpenditureRead])
async def list_expenditures(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await expenditure_crud.list_for_user(db, current_user.id)


@expenditure_router.post("", response_model=ExpenditureRead, status_code=status.HTTP_201_CREATED)
async def create_expenditure(data: ExpenditureCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await expenditure_crud.create(db, current_user.id, data)


@expenditure_router.get("/{expenditureID}", response_model=ExpenditureRead)
async def retrieve_expenditure(expenditureID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    expenditure = await expenditure_crud.get_for_user(db, current_user.id, expenditureID)
    if expenditure is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return expenditure


@expenditure_router.put("/{expenditureID}", response_model=ExpenditureRead)
@expenditure_router.patch("/{expenditureID}", response_model=ExpenditureRead)
async def update_expenditure(
    expenditureID: uuid.UUID,
    data: ExpenditureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenditure = await expenditure_crud.get_for_user(db, current_user.id, expenditureID)
    if expenditure is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return await expenditure_crud.update(db, expenditure, data)


@expenditure_router.delete("/{expenditureID}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expenditure(expenditureID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    expenditure = await expenditure_crud.get_for_user(db, current_user.id, expenditureID)
    if expenditure is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    await expenditure_crud.delete(db, expenditure)


# --------------------------------------------------------------------------
# AI Query  (mirrors tracker/utils.py -> generate_ai_insight)
# --------------------------------------------------------------------------
def _generate_ai_insight_sync(user_query: str, total_income: Decimal, total_expense: Decimal, recent_expenses: list[dict]) -> str:
    net_balance = total_income - total_expense

    system_instruction = (
        "You are TrackFlow AI, an intelligent personal finance assistant. "
        "Analyze the user's provided financial data and answer their question clearly. "
        "Keep your response concise, actionable, and under 3 sentences."
    )
    prompt = (
        f"User Financial Summary:\n"
        f"- Total Income: ${total_income:.2f}\n"
        f"- Total Expenses: ${total_expense:.2f}\n"
        f"- Net Balance: ${net_balance:.2f}\n"
        f"- Recent Transactions: {recent_expenses}\n\n"
        f"User Query: {user_query or 'Give me a brief overview of my financial health and one quick tip.'}"
    )

    api_key = os.getenv("GEMINI_API_KEY")
    fallback = (
        f"Current Balance: ${net_balance:.2f} (Income: ${total_income:.2f}, "
        f"Expenses: ${total_expense:.2f}). Keep tracking to unlock full AI insights!"
    )
    if not api_key:
        return fallback

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    max_retries = 3
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
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


@router.post("/ai-query/", response_model=AIQueryResponse, tags=["dashboard"])
async def ai_query(data: AIQueryRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_income = (
        await db.execute(select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == current_user.id))
    ).scalar_one()
    total_expense = (
        await db.execute(select(func.coalesce(func.sum(Expenditure.amount), 0)).where(Expenditure.user_id == current_user.id))
    ).scalar_one()
    recent = (
        await db.execute(
            select(Expenditure.nameOfItem, Expenditure.amount, Expenditure.category)
            .where(Expenditure.user_id == current_user.id)
            .order_by(Expenditure.created_at.desc())
            .limit(5)
        )
    ).all()
    recent_expenses = [{"nameOfItem": r[0], "amount": float(r[1]), "category": r[2]} for r in recent]

    insight = await asyncio.to_thread(
        _generate_ai_insight_sync, data.query, Decimal(total_income), Decimal(total_expense), recent_expenses
    )
    return AIQueryResponse(insight=insight)


# --------------------------------------------------------------------------
# Dashboard  (mirrors tracker/utils.py -> get_dashboard_data)
# --------------------------------------------------------------------------
@router.get("/dashboard/", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    total_income = (
        await db.execute(select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == user_id))
    ).scalar_one()
    total_expense = (
        await db.execute(select(func.coalesce(func.sum(Expenditure.amount), 0)).where(Expenditure.user_id == user_id))
    ).scalar_one()
    total_balance = Decimal(total_income) - Decimal(total_expense)

    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    income_this_month = (
        await db.execute(
            select(func.coalesce(func.sum(Income.amount), 0)).where(
                Income.user_id == user_id, Income.created_at >= start_of_month
            )
        )
    ).scalar_one()
    expense_this_month = (
        await db.execute(
            select(func.coalesce(func.sum(Expenditure.amount), 0)).where(
                Expenditure.user_id == user_id, Expenditure.created_at >= start_of_month
            )
        )
    ).scalar_one()
    savings_this_month = Decimal(income_this_month) - Decimal(expense_this_month)

    six_months_ago = (now - relativedelta(months=5)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # NOTE: strftime grouping below targets SQLite (the default engine here,
    # matching the original Django db.sqlite3). If you move to Postgres,
    # swap for func.date_trunc('month', Income.created_at).
    income_rows = (
        await db.execute(
            select(func.strftime("%Y-%m", Income.created_at).label("month"), func.sum(Income.amount))
            .where(Income.user_id == user_id, Income.created_at >= six_months_ago)
            .group_by("month")
        )
    ).all()
    expense_rows = (
        await db.execute(
            select(func.strftime("%Y-%m", Expenditure.created_at).label("month"), func.sum(Expenditure.amount))
            .where(Expenditure.user_id == user_id, Expenditure.created_at >= six_months_ago)
            .group_by("month")
        )
    ).all()
    income_by_month = {row[0]: row[1] for row in income_rows}
    expense_by_month = {row[0]: row[1] for row in expense_rows}

    monthly_trend = []
    cursor = six_months_ago
    for _ in range(6):
        key = cursor.strftime("%Y-%m")
        monthly_trend.append(
            {
                "month": key,
                "income": income_by_month.get(key, 0),
                "expense": expense_by_month.get(key, 0),
            }
        )
        cursor += relativedelta(months=1)

    category_rows = (
        await db.execute(
            select(Expenditure.category, func.sum(Expenditure.amount))
            .where(Expenditure.user_id == user_id)
            .group_by(Expenditure.category)
            .order_by(func.sum(Expenditure.amount).desc())
        )
    ).all()
    category_breakdown = [
        {
            "category": row[0],
            "total": row[1],
            "percentage": round((float(row[1]) / float(total_expense)) * 100, 1) if total_expense else 0,
        }
        for row in category_rows
    ]

    return DashboardResponse(
        total_balance=total_balance,
        total_income=total_income,
        total_expense=total_expense,
        income_this_month=income_this_month,
        expense_this_month=expense_this_month,
        savings_this_month=savings_this_month,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown,
    )


router.include_router(income_router)
router.include_router(expenditure_router)