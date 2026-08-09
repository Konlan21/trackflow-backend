"""Mirrors tracker/models.py -> Expenditure, including CATEGORY_CHOICES."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExpenditureCategory(str, enum.Enum):
    FOOD = "FOOD"
    TRANSPORT = "TRANSPORT"
    RENT = "RENT"
    UTILITIES = "UTILITIES"
    ENTERTAINMENT = "ENTERTAINMENT"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    OTHER = "OTHER"


class Expenditure(Base):
    __tablename__ = "expenditures"
    __table_args__ = (
        CheckConstraint("amount >= 1", name="expenditure_amount_min"),
        Index("ix_expenditure_user_category", "user_id", "category"),
        Index("ix_expenditure_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[ExpenditureCategory] = mapped_column(
        Enum(ExpenditureCategory), default=ExpenditureCategory.OTHER, nullable=False
    )
    nameOfItem: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="expenditures")