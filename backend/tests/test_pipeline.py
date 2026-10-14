import os
import json
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base, UploadSessionModel, TransactionModel, AnalysisResultModel
from app.services.pipeline import run_pipeline


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_pipeline_execution(in_memory_db):
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "generic_sample.csv")

    # Create temporary copy of fixture because run_pipeline deletes the input file upon completion
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        with open(fixture_path, "r", encoding="utf-8") as orig:
            f.write(orig.read())
        temp_file_path = f.name

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    upload_session = UploadSessionModel(
        id=session_id,
        filename="generic_sample.csv",
        file_type="csv",
        status="pending",
        uploaded_at=now,
        expires_at=now + timedelta(hours=48),
    )
    in_memory_db.add(upload_session)
    in_memory_db.commit()

    # Run pipeline
    processed = run_pipeline(session_id=session_id, file_path=temp_file_path, db=in_memory_db)

    assert processed.status == "ready"
    assert processed.row_count == 22
    assert processed.error_message is None

    # Check database records
    txns = in_memory_db.query(TransactionModel).filter(TransactionModel.session_id == session_id).all()
    assert len(txns) == 22

    analysis = in_memory_db.query(AnalysisResultModel).filter(AnalysisResultModel.session_id == session_id).first()
    assert analysis is not None
    assert "total_income" in analysis.metrics_json
    insights_list = json.loads(analysis.insights_json)
    assert len(insights_list) >= 3

    # Verify temp file was cleaned up
    assert not os.path.exists(temp_file_path)
