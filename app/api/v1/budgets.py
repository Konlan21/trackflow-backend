"""
Budgets endpoints (Phase 2):
  /user/budgets           (list, create)
  /user/budgets/{id}      (retrieve, update, patch, delete)
  /user/budgets/summary   (current month spend vs limit per category)
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import budget as budget_crud
from app.db.session import get_db
from app.models.budget import Budget
from app.models.expenditure import Expenditure
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetSummaryItem, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
async def list_budgets(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await budget_crud.list_for_user(db, current_user.id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget(data: BudgetCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await budget_crud.create(db, current_user.id, data)


@router.get("/summary")
async def budget_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    budgets = (
        await db.execute(
            select(Budget).where(
                Budget.user_id == current_user.id,
                Budget.month == now.month,
                Budget.year == now.year,
            )
        )
    ).scalars().all()

    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result: dict[str, BudgetSummaryItem] = {}
    for b in budgets:
        spent = (
            await db.execute(
                select(func.coalesce(func.sum(Expenditure.amount), 0)).where(
                    Expenditure.user_id == current_user.id,
                    Expenditure.category == b.category,
                    Expenditure.created_at >= start_of_month,
                )
            )
        ).scalar_one()
        spent = spent or 0
        remaining = b.monthly_limit - spent
        percentage = round((float(spent) / float(b.monthly_limit)) * 100, 1) if b.monthly_limit else 0
        result[b.category.value] = BudgetSummaryItem(
            limit=b.monthly_limit, spent=spent, remaining=remaining, percentage=percentage
        )
    return result


@router.get("/{budgetID}", response_model=BudgetRead)
async def retrieve_budget(budgetID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    budget = await budget_crud.get_for_user(db, current_user.id, budgetID)
    if budget is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return budget


@router.put("/{budgetID}", response_model=BudgetRead)
@router.patch("/{budgetID}", response_model=BudgetRead)
async def update_budget(
    budgetID: uuid.UUID,
    data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = await budget_crud.get_for_user(db, current_user.id, budgetID)
    if budget is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return await budget_crud.update(db, budget, data)


@router.delete("/{budgetID}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budgetID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    budget = await budget_crud.get_for_user(db, current_user.id, budgetID)
    if budget is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    await budget_crud.delete(db, budget)