from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.models.database import get_db, UploadSessionModel, TransactionModel
from app.models.schemas import PaginatedTransactionsResponse, TransactionResponse

router = APIRouter(tags=["Transactions"])


@router.get(
    "/sessions/{id}/transactions",
    response_model=PaginatedTransactionsResponse,
    summary="Get paginated transactions for a session",
)
def get_session_transactions(
    id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: Optional[int] = Query(None, ge=1, le=200, description="Items per page"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Items per page (alias)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query("date", description="Sort by field (date, amount, category)"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
):
    """
    Retrieve transactions associated with an upload session,
    supporting pagination, category filtering, and sorting.
    """
    session = db.query(UploadSessionModel).filter(UploadSessionModel.id == id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' not found.",
        )

    # Resolve items per page
    page_size = per_page or limit or 50

    query = db.query(TransactionModel).filter(TransactionModel.session_id == id)

    # Category filter
    if category:
        query = query.filter(TransactionModel.category.ilike(category))

    # Total count after filter
    total = query.count()

    # Sorting
    sort_column = TransactionModel.date
    if sort_by == "amount":
        sort_column = TransactionModel.amount
    elif sort_by == "category":
        sort_column = TransactionModel.category

    if order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    transactions = query.offset(offset).limit(page_size).all()

    return PaginatedTransactionsResponse(
        data=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        limit=page_size,
    )
