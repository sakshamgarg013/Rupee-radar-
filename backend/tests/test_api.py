import os
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import Base, engine, SessionLocal, get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_upload_and_retrieve_flow():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "generic_sample.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload valid CSV
    response = client.post(
        "/api/v1/upload",
        files={"file": ("generic_sample.csv", io.BytesIO(file_bytes), "text/csv")},
        data={"bank_hint": "hdfc"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    session_id = data.get("id") or data.get("session_id")
    assert session_id is not None
    assert data["status"] == "ready"
    assert data["row_count"] == 22

    # 2. Get session details
    session_res = client.get(f"/api/v1/sessions/{session_id}")
    assert session_res.status_code == 200
    assert session_res.json()["id"] == session_id
    assert session_res.json()["status"] == "ready"

    # 3. Get transactions (paginated)
    txns_res = client.get(f"/api/v1/sessions/{session_id}/transactions?page=1&per_page=10")
    assert txns_res.status_code == 200
    txns_data = txns_res.json()
    assert txns_data["total"] == 22
    assert len(txns_data["data"]) == 10
    assert txns_data["page"] == 1

    # 4. Filter transactions by category
    filter_res = client.get(f"/api/v1/sessions/{session_id}/transactions?category=Food")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    assert filter_data["total"] > 0
    for item in filter_data["data"]:
        assert item["category"] == "Food"

    # 5. Get analytics
    analytics_res = client.get(f"/api/v1/sessions/{session_id}/analytics")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["session_id"] == session_id
    assert analytics_data["metrics"]["total_income"] > 0
    assert analytics_data["metrics"]["total_spend"] > 0
    assert len(analytics_data["top_categories"]) > 0
    assert len(analytics_data["biggest_transactions"]) > 0

    # 6. Get insights
    insights_res = client.get(f"/api/v1/sessions/{session_id}/insights")
    assert insights_res.status_code == 200
    insights_data = insights_res.json()
    assert len(insights_data["insights"]) >= 3


def test_upload_non_csv():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("statement.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert response.status_code == 400
    assert "Only CSV (.csv) files are supported" in response.json()["detail"]


def test_upload_empty_file():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400
    assert "No data found" in response.json()["detail"]


def test_get_nonexistent_session():
    response = client.get("/api/v1/sessions/non-existent-uuid-12345")
    assert response.status_code == 404
