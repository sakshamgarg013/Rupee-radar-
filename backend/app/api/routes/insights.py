import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import get_db, UploadSessionModel, AnalysisResultModel
from app.models.schemas import InsightResponse

router = APIRouter(tags=["Insights"])


@router.get(
    "/sessions/{id}/insights",
    response_model=InsightResponse,
    summary="Get personalized insights for a session",
)
def get_session_insights(id: str, db: Session = Depends(get_db)):
    """
    Retrieve personalized financial insights for an upload session.
    """
    session = db.query(UploadSessionModel).filter(UploadSessionModel.id == id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' not found.",
        )

    analysis = db.query(AnalysisResultModel).filter(AnalysisResultModel.session_id == id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insights not yet generated for session '{id}'.",
        )

    insights = json.loads(analysis.insights_json)
    return InsightResponse(
        session_id=id,
        insights=insights,
    )
