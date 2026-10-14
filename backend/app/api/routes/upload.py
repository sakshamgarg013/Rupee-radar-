import os
import uuid
import shutil
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.database import get_db, UploadSessionModel
from app.models.schemas import UploadSessionResponse
from app.services.pipeline import run_pipeline

router = APIRouter(tags=["Upload & Sessions"])
settings = get_settings()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post(
    "/upload",
    response_model=UploadSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a bank statement CSV file",
)
async def upload_statement(
    file: UploadFile = File(...),
    bank_hint: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a bank statement file (CSV format in Phase 1).
    Validates file format and size, creates an upload session,
    and runs the parsing and analysis pipeline.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # 1. Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext != ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV (.csv) files are supported.",
        )

    # 2. Read and validate content size & non-emptiness
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()

    if not content or len(content.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data found in the uploaded file.",
        )

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # 3. Create UploadSession in DB
    session_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{session_id}.csv")

    try:
        with open(temp_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)

    upload_session = UploadSessionModel(
        id=session_id,
        filename=file.filename,
        file_type="csv",
        bank_hint=bank_hint,
        status="pending",
        uploaded_at=now,
        expires_at=expires_at,
    )
    db.add(upload_session)
    db.commit()
    db.refresh(upload_session)

    # 4. Run pipeline
    try:
        processed_session = run_pipeline(
            session_id=session_id,
            file_path=temp_file_path,
            bank_hint=bank_hint,
            db=db,
        )
        return processed_session
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statement processing failed: {str(err)}",
        )


@router.get(
    "/sessions/{id}",
    response_model=UploadSessionResponse,
    summary="Get upload session status and details",
)
def get_session_status(id: str, db: Session = Depends(get_db)):
    """
    Retrieve status and metadata for a given upload session.
    """
    session = db.query(UploadSessionModel).filter(UploadSessionModel.id == id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' not found.",
        )

    return session
