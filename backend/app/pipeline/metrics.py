from collections import defaultdict
from datetime import date
from typing import List, Dict, Any, Optional


def compute_metrics(txns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute financial summary metrics, category totals, and monthly trends from transactions.
    """
    if not txns:
        return {
            "metrics": {
                "total_income": 0.0,
                "total_spend": 0.0,
                "savings": 0.0,
                "savings_rate": 0.0,
                "transaction_count": 0,
                "date_range": None,
                "monthly_spend": {},
            },
            "top_categories": [],
            "biggest_transactions": [],
            "category_breakdown": [],
            "monthly_spend": {},
        }

    total_income = 0.0
    total_spend = 0.0
    min_date: Optional[date] = None
    max_date: Optional[date] = None

    category_totals: Dict[str, float] = defaultdict(float)
    category_counts: Dict[str, int] = defaultdict(int)
    monthly_spend_map: Dict[str, float] = defaultdict(float)
    debit_txns: List[Dict[str, Any]] = []

    for txn in txns:
        txn_date = txn.get("date")
        if isinstance(txn_date, str):
            from datetime import datetime
            txn_date = datetime.strptime(txn_date[:10], "%Y-%m-%d").date()

        if txn_date:
            if min_date is None or txn_date < min_date:
                min_date = txn_date
            if max_date is None or txn_date > max_date:
                max_date = txn_date

        amount = float(txn.get("amount", 0.0))
        txn_type = txn.get("type", "debit")
        category = txn.get("category", "Other")

        if txn_type == "credit":
            total_income += abs(amount)
        else:
            debit_amt = abs(amount)
            total_spend += debit_amt
            category_totals[category] += debit_amt
            category_counts[category] += 1
            debit_txns.append(txn)

            if txn_date:
                month_key = txn_date.strftime("%Y-%m")
                monthly_spend_map[month_key] += debit_amt

    total_income = round(total_income, 2)
    total_spend = round(total_spend, 2)
    savings = round(total_income - total_spend, 2)
    savings_rate = round((savings / total_income) * 100, 2) if total_income > 0 else 0.0

    # Top categories (sorted descending by debit spend)
    category_breakdown = []
    for cat, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        cat_total = round(total, 2)
        pct = round((cat_total / total_spend) * 100, 2) if total_spend > 0 else 0.0
        category_breakdown.append({
            "category": cat,
            "total": cat_total,
            "percentage": pct,
            "count": category_counts[cat],
        })

    top_categories = category_breakdown[:5]

    # Biggest debit transactions (top 5 largest spend)
    sorted_debits = sorted(debit_txns, key=lambda t: abs(float(t.get("amount", 0.0))), reverse=True)
    biggest_transactions = []
    for t in sorted_debits[:5]:
        b_date = t.get("date")
        if isinstance(b_date, str):
            from datetime import datetime
            b_date = datetime.strptime(b_date[:10], "%Y-%m-%d").date()

        biggest_transactions.append({
            "amount": round(abs(float(t.get("amount", 0.0))), 2),
            "description": t.get("description_clean") or t.get("description_raw") or "Unknown",
            "date": b_date,
            "category": t.get("category", "Other"),
        })

    # Sort monthly spend chronologically
    sorted_monthly_spend = {
        m: round(amt, 2) for m, amt in sorted(monthly_spend_map.items())
    }

    date_range = None
    if min_date and max_date:
        date_range = {
            "from": min_date.isoformat(),
            "to": max_date.isoformat(),
        }

    metrics_summary = {
        "total_income": total_income,
        "total_spend": total_spend,
        "savings": savings,
        "savings_rate": savings_rate,
        "transaction_count": len(txns),
        "date_range": date_range,
        "monthly_spend": sorted_monthly_spend,
    }

    return {
        "metrics": metrics_summary,
        "top_categories": top_categories,
        "biggest_transactions": biggest_transactions,
        "category_breakdown": category_breakdown,
        "monthly_spend": sorted_monthly_spend,
    }
