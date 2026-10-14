from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import (
    create_engine,
    String,
    Float,
    Integer,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session,
)
from app.config import get_settings

settings = get_settings()

# Engine setup: check_same_thread=False is needed for SQLite with FastAPI multi-threading
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class UploadSessionModel(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # csv | xlsx | pdf
    bank_hint: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending | parsing | processing | ready | failed
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    transactions: Mapped[List["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="session", cascade="all, delete-orphan"
    )
    recurring_groups: Mapped[List["RecurringGroupModel"]] = relationship(
        "RecurringGroupModel", back_populates="session", cascade="all, delete-orphan"
    )
    analysis_result: Mapped[Optional["AnalysisResultModel"]] = relationship(
        "AnalysisResultModel", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # signed: negative for debits, positive for credits
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # credit | debit
    balance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Other")
    category_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recurring_groups.id", ondelete="SET NULL"), nullable=True
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["UploadSessionModel"] = relationship("UploadSessionModel", back_populates="transactions")
    recurring_group: Mapped[Optional["RecurringGroupModel"]] = relationship("RecurringGroupModel", back_populates="transactions")

    __table_args__ = (
        Index("idx_txn_session_date", "session_id", "date"),
        Index("idx_txn_session_category", "session_id", "category"),
    )


class RecurringGroupModel(Base):
    __tablename__ = "recurring_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly | monthly | quarterly | yearly | unknown
    typical_amount: Mapped[float] = mapped_column(Float, nullable=False)
    last_seen_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    session: Mapped["UploadSessionModel"] = relationship("UploadSessionModel", back_populates="recurring_groups")
    transactions: Mapped[List["TransactionModel"]] = relationship("TransactionModel", back_populates="recurring_group")

    __table_args__ = (
        Index("idx_recurring_session", "session_id"),
    )


class AnalysisResultModel(Base):
    __tablename__ = "analysis_results"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    top_categories_json: Mapped[str] = mapped_column(Text, nullable=False)
    biggest_transactions_json: Mapped[str] = mapped_column(Text, nullable=False)
    insights_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session: Mapped["UploadSessionModel"] = relationship("UploadSessionModel", back_populates="analysis_result")


def init_db() -> None:
    """Create all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for obtaining a database session in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
