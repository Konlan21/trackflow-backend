"""Mirrors the dict shape returned by tracker/utils.py -> get_dashboard_data()."""
from decimal import Decimal

from pydantic import BaseModel


class MonthlyTrendItem(BaseModel):
    month: str
    income: Decimal
    expense: Decimal


class CategoryBreakdownItem(BaseModel):
    category: str
    total: Decimal
    percentage: float


class DashboardResponse(BaseModel):
    total_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    income_this_month: Decimal
    expense_this_month: Decimal
    savings_this_month: Decimal
    monthly_trend: list[MonthlyTrendItem]
    category_breakdown: list[CategoryBreakdownItem]


class AIQueryRequest(BaseModel):
    query: str = ""


class AIQueryResponse(BaseModel):
    insight: str