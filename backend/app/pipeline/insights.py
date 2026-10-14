from typing import List, Dict, Any

from app.config import get_settings
from app.services.groq_client import GroqClient
from app.utils.currency import format_inr

settings = get_settings()


def generate_insights(metrics_data: Dict[str, Any], txns: List[Dict[str, Any]]) -> List[str]:
    """
    Generate deterministic template insights and append Groq narrative insights when configured.
    Guarantees >= 3 insights for non-empty statement data.
    """
    if not txns:
        return [
            "No transactions found to generate insights.",
            "Upload a statement with valid transactions to view spending patterns.",
            "Your financial summary will appear here once data is processed.",
        ]

    metrics = metrics_data.get("metrics", {})
    top_categories = metrics_data.get("top_categories", [])
    biggest_txns = metrics_data.get("biggest_transactions", [])
    monthly_spend = metrics_data.get("monthly_spend", {})

    total_income = metrics.get("total_income", 0.0)
    total_spend = metrics.get("total_spend", 0.0)
    savings = metrics.get("savings", 0.0)
    savings_rate = metrics.get("savings_rate", 0.0)
    txn_count = metrics.get("transaction_count", len(txns))

    insights: List[str] = []

    if top_categories:
        top_cat = top_categories[0]
        cat_name = top_cat["category"]
        cat_total = top_cat["total"]
        pct = top_cat.get("percentage", 0.0)
        formatted_cat_amt = format_inr(cat_total)
        insights.append(
            f"You spent {formatted_cat_amt} on {cat_name} ({pct}% of spend) — your largest spending category."
        )

    if biggest_txns:
        biggest = biggest_txns[0]
        amt = biggest["amount"]
        desc = biggest["description"]
        b_date = biggest.get("date")
        date_str = b_date.strftime("%d %b %Y") if hasattr(b_date, "strftime") else str(b_date)
        formatted_amt = format_inr(amt)
        insights.append(
            f"Your biggest transaction was {formatted_amt} for '{desc}' on {date_str}."
        )

    if total_income > 0:
        formatted_savings = format_inr(savings)
        if savings >= 0:
            insights.append(
                f"Your savings rate is {savings_rate}% — you saved {formatted_savings} this period."
            )
        else:
            insights.append(
                f"Your spending exceeded income by {format_inr(abs(savings))} this period."
            )
    else:
        insights.append(
            f"Total expenditure across this period was {format_inr(total_spend)}."
        )

    if len(monthly_spend) >= 2:
        highest_month = max(monthly_spend.items(), key=lambda x: x[1])
        formatted_m_amt = format_inr(highest_month[1])
        insights.append(
            f"Your highest spending month was {highest_month[0]} at {formatted_m_amt}."
        )

    if txn_count > 0:
        avg_spend = total_spend / txn_count if total_spend > 0 else 0.0
        formatted_avg = format_inr(avg_spend)
        insights.append(
            f"You made {txn_count} transactions averaging {formatted_avg} in spending per transaction."
        )

    if len(top_categories) >= 2 and len(insights) < 3:
        second_cat = top_categories[1]
        formatted_second = format_inr(second_cat["total"])
        insights.append(
            f"Your second highest category was {second_cat['category']} with {formatted_second} spent."
        )

    if settings.GROQ_API_KEY:
        client = GroqClient(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
        ai_insights = client.generate_narrative_insights(metrics_data.get("metrics", {}))
        if ai_insights:
            insights.extend([f"AI: {item}" for item in ai_insights])

    if len(insights) < 3:
        fallback = [
            "Your budget remains most stable when essential expenses stay under control.",
            "A balanced cash flow approach helps keep recurring costs predictable.",
            "Reviewing larger transactions monthly helps highlight spend clusters early.",
        ]
        for item in fallback:
            if len(insights) >= 3:
                break
            insights.append(item)

    return insights
