from datetime import date
from app.pipeline.metrics import compute_metrics


def test_compute_metrics():
    txns = [
        {"date": date(2024, 5, 1), "amount": 80000.0, "type": "credit", "category": "Salary", "description_clean": "SALARY"},
        {"date": date(2024, 5, 2), "amount": -20000.0, "type": "debit", "category": "Rent", "description_clean": "RENT"},
        {"date": date(2024, 5, 3), "amount": -10000.0, "type": "debit", "category": "EMI", "description_clean": "EMI"},
        {"date": date(2024, 5, 4), "amount": -500.0, "type": "debit", "category": "Food", "description_clean": "SWIGGY"},
    ]

    result = compute_metrics(txns)
    metrics = result["metrics"]

    assert metrics["total_income"] == 80000.0
    assert metrics["total_spend"] == 30500.0
    assert metrics["savings"] == 49500.0
    assert metrics["savings_rate"] == round((49500.0 / 80000.0) * 100, 2)
    assert metrics["transaction_count"] == 4
    assert metrics["date_range"] == {"from": "2024-05-01", "to": "2024-05-04"}

    top_categories = result["top_categories"]
    assert len(top_categories) == 3
    assert top_categories[0]["category"] == "Rent"
    assert top_categories[0]["total"] == 20000.0
    assert top_categories[1]["category"] == "EMI"

    biggest = result["biggest_transactions"]
    assert len(biggest) == 3
    assert biggest[0]["amount"] == 20000.0
    assert biggest[0]["description"] == "RENT"
