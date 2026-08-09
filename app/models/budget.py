"""Budget model — mirrors the same style as Expenditure (tracker/models.py)."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, UniqueConstraint, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.expenditure import ExpenditureCategory


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("monthly_limit >= 0", name="budget_monthly_limit_min"),
        CheckConstraint("month >= 1 AND month <= 12", name="budget_month_range"),
        CheckConstraint("year >= 2000", name="budget_year_min"),
        UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_category_month_year"),
        Index("ix_budget_user_month_year", "user_id", "month", "year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[ExpenditureCategory] = mapped_column(
        Enum(ExpenditureCategory), default=ExpenditureCategory.OTHER, nullable=False
    )
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="budgets")