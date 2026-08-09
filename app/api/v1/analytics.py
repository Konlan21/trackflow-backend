"""
Analytics endpoints (Phase 4):
  GET /user/analytics/monthly        -> last 6 months income/expense trend
  GET /user/analytics/categories     -> expense total per category
  GET /user/analytics/daily          -> daily spending, current month
  GET /user/analytics/top-expenses   -> top 5 single expenses
  GET /user/analytics/comparison     -> this month vs last month
"""
from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.expenditure import Expenditure
from app.models.income import Income
from app.models.user import User
from app.schemas.analytics import (
    CategoryAnalyticsItem,
    DailySpendingItem,
    MonthlyAnalyticsItem,
    MonthlyComparisonResponse,
    TopExpenseItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/monthly", response_model=list[MonthlyAnalyticsItem])
async def monthly_trend(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    now = datetime.utcnow()
    six_months_ago = (now - relativedelta(months=5)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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

    result = []
    cursor = six_months_ago
    for _ in range(6):
        key = cursor.strftime("%Y-%m")
        result.append(
            MonthlyAnalyticsItem(
                month=cursor.strftime("%b"),
                income=income_by_month.get(key, 0),
                expense=expense_by_month.get(key, 0),
            )
        )
        cursor += relativedelta(months=1)
    return result


@router.get("/categories", response_model=list[CategoryAnalyticsItem])
async def category_breakdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        await db.execute(
            select(Expenditure.category, func.sum(Expenditure.amount))
            .where(Expenditure.user_id == current_user.id)
            .group_by(Expenditure.category)
            .order_by(func.sum(Expenditure.amount).desc())
        )
    ).all()
    return [CategoryAnalyticsItem(category=row[0].value, amount=row[1]) for row in rows]


@router.get("/daily", response_model=list[DailySpendingItem])
async def daily_spending(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        await db.execute(
            select(func.strftime("%Y-%m-%d", Expenditure.created_at).label("day"), func.sum(Expenditure.amount))
            .where(Expenditure.user_id == current_user.id, Expenditure.created_at >= start_of_month)
            .group_by("day")
            .order_by("day")
        )
    ).all()
    return [DailySpendingItem(date=row[0], amount=row[1]) for row in rows]


@router.get("/top-expenses", response_model=list[TopExpenseItem])
async def top_expenses(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        await db.execute(
            select(Expenditure)
            .where(Expenditure.user_id == current_user.id)
            .order_by(Expenditure.amount.desc())
            .limit(5)
        )
    ).scalars().all()
    return [
        TopExpenseItem(
            id=str(e.id),
            nameOfItem=e.nameOfItem,
            category=e.category.value,
            amount=e.amount,
            created_at=e.created_at.isoformat(),
        )
        for e in rows
    ]


@router.get("/comparison", response_model=MonthlyComparisonResponse)
async def monthly_comparison(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    now = datetime.utcnow()
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = start_of_this_month - relativedelta(months=1)

    async def sums(model, start, end):
        result = await db.execute(
            select(func.coalesce(func.sum(model.amount), 0)).where(
                model.user_id == user_id, model.created_at >= start, model.created_at < end
            )
        )
        return result.scalar_one()

    current_income = await sums(Income, start_of_this_month, now)
    current_expense = await sums(Expenditure, start_of_this_month, now)
    previous_income = await sums(Income, start_of_last_month, start_of_this_month)
    previous_expense = await sums(Expenditure, start_of_last_month, start_of_this_month)

    def pct_change(current, previous):
        if not previous:
            return 100.0 if current else 0.0
        return round((float(current) - float(previous)) / float(previous) * 100, 1)

    return MonthlyComparisonResponse(
        current_month=start_of_this_month.strftime("%b %Y"),
        previous_month=start_of_last_month.strftime("%b %Y"),
        current_income=current_income,
        current_expense=current_expense,
        previous_income=previous_income,
        previous_expense=previous_expense,
        income_change_percentage=pct_change(current_income, previous_income),
        expense_change_percentage=pct_change(current_expense, previous_expense),
    )