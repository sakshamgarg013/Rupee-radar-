from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class CategoryEnum(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    EMI = "EMI"
    SUBSCRIPTIONS = "Subscriptions"
    SALARY = "Salary"
    RENT = "Rent"
    INVESTMENTS = "Investments"
    OTHER = "Other"


class TransactionTypeEnum(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class FrequencyEnum(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    UNKNOWN = "unknown"


# --- Session Schemas ---

class UploadSessionBase(BaseModel):
    filename: str
    file_type: str
    bank_hint: Optional[str] = None


class UploadSessionCreate(UploadSessionBase):
    pass


class UploadSessionResponse(UploadSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: Optional[str] = None
    status: str
    uploaded_at: datetime
    expires_at: datetime
    error_message: Optional[str] = None
    row_count: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        if self.session_id is None and self.id is not None:
            self.session_id = self.id


# --- Transaction Schemas ---

class TransactionBase(BaseModel):
    date: date
    description_raw: str
    description_clean: Optional[str] = None
    amount: float
    type: TransactionTypeEnum
    balance: Optional[float] = None
    category: CategoryEnum = CategoryEnum.OTHER
    category_confidence: float = 0.0
    is_recurring: bool = False
    recurring_group_id: Optional[int] = None
    metadata_json: Optional[str] = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str


class TransactionUpdate(BaseModel):
    category: CategoryEnum


class PaginatedTransactionsResponse(BaseModel):
    data: List[TransactionResponse]
    total: int
    page: int
    limit: int


# --- Recurring Group Schemas ---

class RecurringGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    label: str
    category: str
    frequency: FrequencyEnum
    typical_amount: float
    last_seen_date: Optional[date] = None
    confidence: float
    transaction_ids: Optional[List[int]] = None


# --- Analytics & Insights Schemas ---

class DateRange(BaseModel):
    from_date: date = Field(..., alias="from")
    to_date: date = Field(..., alias="to")


class FinancialMetrics(BaseModel):
    total_income: float
    total_spend: float
    savings: float
    savings_rate: float
    transaction_count: int
    date_range: Optional[DateRange] = None


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    percentage: float
    count: int


class BiggestTransaction(BaseModel):
    amount: float
    description: str
    date: date
    category: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    metrics: FinancialMetrics
    top_categories: List[CategoryBreakdown]
    biggest_transactions: List[BiggestTransaction]
    insights: List[str]
    generated_at: datetime


class InsightResponse(BaseModel):
    session_id: str
    insights: List[str]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
