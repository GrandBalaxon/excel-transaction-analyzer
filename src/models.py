from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class DimCard(Base):
    """Bank card dimension."""
    __tablename__ = "dim_cards"

    card_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    last_digits: Mapped[str] = mapped_column(String(4))

    transactions: Mapped[list[FactTransaction]] = relationship(back_populates="card")


class DimCategory(Base):
    """Spending category dimension."""
    __tablename__ = "dim_categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    transactions: Mapped[list[FactTransaction]] = relationship(back_populates="category")


class DimDate(Base):
    """Date dimension (calendar)."""
    __tablename__ = "dim_dates"

    date_id: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)
    weekday: Mapped[int] = mapped_column(Integer)

    transactions: Mapped[list[FactTransaction]] = relationship(back_populates="date")


class FactTransaction(Base):
    """Fact table (the transactions themselves)."""
    __tablename__ = "fact_transactions"

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    date_id: Mapped[datetime.date] = mapped_column(ForeignKey("dim_dates.date_id"))
    card_id: Mapped[str | None] = mapped_column(ForeignKey("dim_cards.card_id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("dim_categories.category_id"))

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)

    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    payment_currency_code: Mapped[str] = mapped_column(String(3), nullable=False)

    amount_rub: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    cashback: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00")
    )

    status: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(255))

    date: Mapped[DimDate] = relationship(back_populates="transactions")
    card: Mapped[DimCard | None] = relationship(back_populates="transactions")
    category: Mapped[DimCategory] = relationship(back_populates="transactions")
