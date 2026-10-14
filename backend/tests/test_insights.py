from datetime import date
from app.pipeline.metrics import compute_metrics
from app.pipeline.insights import generate_insights


def test_generate_insights_at_least_three():
    txns = [
        {"date": date(2024, 5, 1), "amount": 80000.0, "type": "credit", "category": "Salary", "description_clean": "INFOSYS SALARY"},
        {"date": date(2024, 5, 2), "amount": -20000.0, "type": "debit", "category": "Rent", "description_clean": "HOUSE RENT"},
        {"date": date(2024, 5, 3), "amount": -10000.0, "type": "debit", "category": "EMI", "description_clean": "HOME LOAN EMI"},
        {"date": date(2024, 5, 4), "amount": -500.0, "type": "debit", "category": "Food", "description_clean": "SWIGGY"},
    ]

    metrics_data = compute_metrics(txns)
    insights = generate_insights(metrics_data, txns)

    assert len(insights) >= 3
    # Check that ₹ symbol and amounts are present
    assert any("₹" in ins for ins in insights)
    assert any("Rent" in ins for ins in insights)
    assert any("HOUSE RENT" in ins for ins in insights)
