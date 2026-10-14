import re
from typing import List, Dict, Any, Optional, Tuple

from app.config import get_settings
from app.models.schemas import CategoryEnum
from app.services.groq_client import GroqClient
from app.utils.merchant_dict import find_merchant

settings = get_settings()

# Rule patterns: (regex pattern, CategoryEnum, confidence)
KEYWORD_RULES: List[Tuple[str, CategoryEnum, float]] = [
    # Salary
    (r"\b(?:SALARY|PAYROLL|MONTHLY\s+SAL|NEFT\s+CREDIT\s+SALARY|STIPEND|WAGES)\b", CategoryEnum.SALARY, 0.95),
    
    # EMI & Loans
    (r"\b(?:EMI|HOME\s+LOAN|CAR\s+LOAN|PERSONAL\s+LOAN|EDUCATION\s+LOAN|LOAN\s+REPAYMENT|BAJAJ\s+FINSERV|HDFC\s+LOAN|ICICI\s+LOAN|CREDIT\s+CARD\s+PAYMENT|CRED\s+CLUB)\b", CategoryEnum.EMI, 0.90),
    
    # Rent
    (r"\b(?:RENT|HOUSE\s+RENT|FLAT\s+RENT|ROOM\s+RENT|PG\s+RENT|NOBROKER\s+RENT|MYGATE\s+RENT)\b", CategoryEnum.RENT, 0.90),
    
    # Investments
    (r"\b(?:SIP|MUTUAL\s+FUND|MF\s+PURCHASE|NPS|PPF|SECURITIES|ZERODHA|GROWW|UPSTOX|ANGEL\s+ONE|INDMONEY|KFINTECH|CAMS|EQUITY|STOCKS)\b", CategoryEnum.INVESTMENTS, 0.90),
    
    # Subscriptions
    (r"\b(?:NETFLIX|SPOTIFY|YOUTUBE\s+PREMIUM|HOTSTAR|DISNEY|PRIME\s+VIDEO|APPLE\s+SERVICES|GAANA|SONYLIV|ZEE5|CHATGPT|OPENAI)\b", CategoryEnum.SUBSCRIPTIONS, 0.90),
    
    # Bills & Utilities
    (r"\b(?:ELECTRICITY|WATER\s+BILL|GAS\s+BILL|BROADBAND|BILLPAY|RECHARGE|AIRTEL|JIO\s+PREPAID|JIO\s+POSTPAID|BESCOM|TATA\s+POWER|IGL|MGL|ADANI\s+GAS|DTH|MOBILE\s+RECHARGE)\b", CategoryEnum.BILLS, 0.85),
    
    # Food & Dining
    (r"\b(?:SWIGGY|ZOMATO|DOMINOS|MCDONALD|STARBUCKS|KFC|BURGER\s+KING|SUBWAY|PIZZA|BLINKIT|ZEPTO|INSTAMART|BIGBASKET|CAFE|RESTAURANT|BAKERY|DHABA|BIRYANI)\b", CategoryEnum.FOOD, 0.85),
    
    # Travel & Commute
    (r"\b(?:UBER|OLA|IRCTC|RAILWAY|MAKEMYTRIP|GOIBIBO|RAPIDO|INDIGO|AIR\s+INDIA|SPICEJET|RED\s+BUS|FASTAG|TOLL|PETROL|FUEL|HPCL|BPCL|IOCL|SHELL)\b", CategoryEnum.TRAVEL, 0.85),
    
    # Shopping & E-Commerce
    (r"\b(?:AMAZON|FLIPKART|MYNTRA|AJIO|NYKAA|TATA\s+CLIQ|MEESHO|CROMA|RELIANCE\s+DIGITAL|DECATHLON|LENSKART|ZUDIO|WESTSIDE|H&M|ZARA|MALL|SUPERMARKET|MART)\b", CategoryEnum.SHOPPING, 0.85),
]


def match_rule_engine(description: str) -> Optional[Tuple[CategoryEnum, float]]:
    """Match description against keyword regex rules."""
    desc_upper = description.upper()
    for pattern, category, confidence in KEYWORD_RULES:
        if re.search(pattern, desc_upper):
            return category, confidence
    return None


def categorize_single(txn: Dict[str, Any]) -> Tuple[str, float]:
    """
    Categorize a single transaction using rules, dictionary, heuristics, and fallback.
    Returns:
        (category_name, confidence)
    """
    desc_clean = txn.get("description_clean", "")
    desc_raw = txn.get("description_raw", "")
    amount = txn.get("amount", 0.0)
    txn_type = txn.get("type", "debit")

    # Tier 1: Rule Engine
    rule_match = match_rule_engine(desc_clean) or match_rule_engine(desc_raw)
    if rule_match:
        return rule_match[0].value, rule_match[1]

    # Tier 2: Merchant Dictionary Lookup
    merchant_match = find_merchant(desc_clean) or find_merchant(desc_raw)
    if merchant_match:
        # merchant_match returns (merchant_name, category, confidence)
        return merchant_match[1], merchant_match[2]

    # Credit transaction heuristic: large recurring or salary credits
    if txn_type == "credit":
        if amount >= 25000:
            # High amount credit without merchant is very often salary
            return CategoryEnum.SALARY.value, 0.70
        elif any(k in desc_clean.upper() for k in ["DIVIDEND", "INTEREST", "INT.PD", "INT REC"]):
            return CategoryEnum.INVESTMENTS.value, 0.85

    # Tier 4: Fallback
    return CategoryEnum.OTHER.value, 0.0


def categorize_transactions(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign category and confidence score to each transaction.
    Includes optional Groq fallback for unmatched transactions when configured.
    """
    categorized_txns: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []

    for txn in txns:
        category, confidence = categorize_single(txn)
        updated_txn = dict(txn)
        updated_txn["category"] = category
        updated_txn["category_confidence"] = confidence

        if category == CategoryEnum.OTHER.value and confidence == 0.0:
            unmatched.append(updated_txn)
        categorized_txns.append(updated_txn)

    if settings.GROQ_API_KEY and unmatched:
        client = GroqClient(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
        llm_results = client.categorize_batch(unmatched)
        llm_map = {str(item.get("id")): item for item in llm_results if item.get("id") is not None}
        if llm_map:
            for updated_txn in categorized_txns:
                txn_key = str(updated_txn.get("id") or updated_txn.get("description_clean") or updated_txn.get("description_raw") or "")
                if txn_key in llm_map:
                    llm_item = llm_map[txn_key]
                    confidence = float(llm_item.get("confidence", 0.0) or 0.0)
                    if confidence >= 0.6:
                        updated_txn["category"] = str(llm_item.get("category") or CategoryEnum.OTHER.value)
                        updated_txn["category_confidence"] = confidence
                    else:
                        updated_txn["category"] = CategoryEnum.OTHER.value
                        updated_txn["category_confidence"] = 0.0

    return categorized_txns
