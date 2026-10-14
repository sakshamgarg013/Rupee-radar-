import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import get_db, UploadSessionModel, AnalysisResultModel
from app.models.schemas import (
    AnalysisResultResponse,
    FinancialMetrics,
    CategoryBreakdown,
    BiggestTransaction,
)

router = APIRouter(tags=["Analytics"])


@router.get(
    "/sessions/{id}/analytics",
    response_model=AnalysisResultResponse,
    summary="Get aggregated financial analytics for a session",
)
def get_session_analytics(id: str, db: Session = Depends(get_db)):
    """
    Retrieve computed metrics, top category breakdown, and largest transactions for an upload session.
    """
    session = db.query(UploadSessionModel).filter(UploadSessionModel.id == id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' not found.",
        )

    if session.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not ready for session '{id}' (current status: {session.status}).",
        )

    analysis = db.query(AnalysisResultModel).filter(AnalysisResultModel.session_id == id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis results not found for session '{id}'.",
        )

    metrics_data = json.loads(analysis.metrics_json)
    top_categories_data = json.loads(analysis.top_categories_json)
    biggest_txns_data = json.loads(analysis.biggest_transactions_json)
    insights_data = json.loads(analysis.insights_json)

    return AnalysisResultResponse(
        session_id=analysis.session_id,
        metrics=FinancialMetrics(**metrics_data),
        top_categories=[CategoryBreakdown(**c) for c in top_categories_data],
        biggest_transactions=[BiggestTransaction(**b) for b in biggest_txns_data],
        insights=insights_data,
        generated_at=analysis.generated_at,
    )
