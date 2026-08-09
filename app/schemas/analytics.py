"""Analytics response shapes (Phase 4)."""
from decimal import Decimal

from pydantic import BaseModel


class MonthlyAnalyticsItem(BaseModel):
    month: str
    income: Decimal
    expense: Decimal


class CategoryAnalyticsItem(BaseModel):
    category: str
    amount: Decimal


class DailySpendingItem(BaseModel):
    date: str
    amount: Decimal


class TopExpenseItem(BaseModel):
    id: str
    nameOfItem: str
    category: str
    amount: Decimal
    created_at: str


class MonthlyComparisonResponse(BaseModel):
    current_month: str
    previous_month: str
    current_income: Decimal
    current_expense: Decimal
    previous_income: Decimal
    previous_expense: Decimal
    income_change_percentage: float
    expense_change_percentage: float