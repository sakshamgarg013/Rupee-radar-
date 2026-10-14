import os
import json
import logging
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import SessionLocal, UploadSessionModel, TransactionModel, AnalysisResultModel
from app.parsers import get_parser
from app.pipeline.cleaner import clean_transactions
from app.pipeline.categorizer import categorize_transactions
from app.pipeline.metrics import compute_metrics
from app.pipeline.insights import generate_insights

logger = logging.getLogger(__name__)


def json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def run_pipeline(session_id: str, file_path: str, bank_hint: Optional[str] = None, db: Optional[Session] = None) -> UploadSessionModel:
    """
    Executes the RupeeRadar MVP processing pipeline:
    1. Select parser & parse file
    2. Clean and normalize transactions
    3. Categorize transactions (rule engine & dictionary)
    4. Compute metrics and aggregations
    5. Generate template insights
    6. Persist transactions & analysis results to database
    7. Delete temporary raw upload file
    """
    owns_db = False
    if db is None:
        db = SessionLocal()
        owns_db = True

    try:
        session = db.query(UploadSessionModel).filter(UploadSessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session with id {session_id} not found in database.")

        # Stage 1: Parsing
        session.status = "parsing"
        db.commit()

        logger.info(f"[{session_id}] Selecting parser and parsing statement: {file_path}")
        parser = get_parser(file_path, bank_hint=bank_hint)
        raw_txns = parser.parse(file_path)

        if not raw_txns:
            raise ValueError("No transaction records found in the uploaded file.")

        # Stage 2: Processing & Cleaning
        session.status = "processing"
        db.commit()

        logger.info(f"[{session_id}] Cleaning {len(raw_txns)} raw transactions")
        cleaned_txns = clean_transactions(raw_txns)

        # Stage 3: Categorization
        logger.info(f"[{session_id}] Categorizing transactions")
        categorized_txns = categorize_transactions(cleaned_txns)

        # Stage 4: Recurring Detection (Deferred to Phase 4)

        # Stage 5: Metrics & Aggregations
        logger.info(f"[{session_id}] Computing financial metrics")
        metrics_data = compute_metrics(categorized_txns)

        # Stage 6: Insights Generation
        logger.info(f"[{session_id}] Generating insights")
        insights = generate_insights(metrics_data, categorized_txns)

        # Stage 7: Persist results
        logger.info(f"[{session_id}] Persisting {len(categorized_txns)} transactions and analysis to DB")

        # 1. Insert Transaction rows
        for txn_dict in categorized_txns:
            txn_model = TransactionModel(
                session_id=session_id,
                date=txn_dict["date"],
                description_raw=txn_dict["description_raw"],
                description_clean=txn_dict.get("description_clean"),
                amount=txn_dict["amount"],
                type=txn_dict["type"],
                balance=txn_dict.get("balance"),
                category=txn_dict.get("category", "Other"),
                category_confidence=txn_dict.get("category_confidence", 0.0),
                is_recurring=False,
                recurring_group_id=None,
                metadata_json=txn_dict.get("metadata_json"),
            )
            db.add(txn_model)

        # 2. Insert or update AnalysisResult row
        existing_result = db.query(AnalysisResultModel).filter(AnalysisResultModel.session_id == session_id).first()
        if existing_result:
            db.delete(existing_result)

        analysis_result = AnalysisResultModel(
            session_id=session_id,
            metrics_json=json.dumps(metrics_data["metrics"], default=json_serial),
            top_categories_json=json.dumps(metrics_data["top_categories"], default=json_serial),
            biggest_transactions_json=json.dumps(metrics_data["biggest_transactions"], default=json_serial),
            insights_json=json.dumps(insights, default=json_serial),
            generated_at=datetime.now(timezone.utc),
        )
        db.add(analysis_result)

        # 3. Update UploadSession status to ready
        session.status = "ready"
        session.row_count = len(categorized_txns)
        session.error_message = None
        db.commit()
        db.refresh(session)

        # Cleanup raw upload file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[{session_id}] Deleted temporary uploaded file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {file_path}: {e}")

        return session

    except Exception as e:
        logger.exception(f"[{session_id}] Pipeline execution failed: {str(e)}")
        if db:
            db.rollback()
            try:
                failed_session = db.query(UploadSessionModel).filter(UploadSessionModel.id == session_id).first()
                if failed_session:
                    failed_session.status = "failed"
                    failed_session.error_message = str(e)
                    db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to record failure status in session: {commit_err}")

        # Clean up temporary file on failure as well
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        raise

    finally:
        if owns_db:
            db.close()
