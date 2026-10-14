import re
import difflib
from typing import Optional, Tuple
from app.models.schemas import CategoryEnum

# Curated dictionary of 60+ common Indian merchants and platforms mapped to their canonical category
MERCHANT_CATEGORIES = {
    # --- Food & Dining & Quick Commerce ---
    "swiggy": CategoryEnum.FOOD.value,
    "zomato": CategoryEnum.FOOD.value,
    "dominos": CategoryEnum.FOOD.value,
    "mcdonald": CategoryEnum.FOOD.value,
    "kfc": CategoryEnum.FOOD.value,
    "burger king": CategoryEnum.FOOD.value,
    "starbucks": CategoryEnum.FOOD.value,
    "subway": CategoryEnum.FOOD.value,
    "pizza hut": CategoryEnum.FOOD.value,
    "blinkit": CategoryEnum.FOOD.value,
    "zepto": CategoryEnum.FOOD.value,
    "instamart": CategoryEnum.FOOD.value,
    "bigbasket": CategoryEnum.FOOD.value,
    "dunzo": CategoryEnum.FOOD.value,
    "eatclub": CategoryEnum.FOOD.value,
    "faasos": CategoryEnum.FOOD.value,
    "behrouz": CategoryEnum.FOOD.value,
    "haldiram": CategoryEnum.FOOD.value,
    "chaayos": CategoryEnum.FOOD.value,
    "chai point": CategoryEnum.FOOD.value,

    # --- Travel & Commute ---
    "uber": CategoryEnum.TRAVEL.value,
    "ola": CategoryEnum.TRAVEL.value,
    "rapido": CategoryEnum.TRAVEL.value,
    "irctc": CategoryEnum.TRAVEL.value,
    "makemytrip": CategoryEnum.TRAVEL.value,
    "goibibo": CategoryEnum.TRAVEL.value,
    "redbus": CategoryEnum.TRAVEL.value,
    "indigo": CategoryEnum.TRAVEL.value,
    "air india": CategoryEnum.TRAVEL.value,
    "spicejet": CategoryEnum.TRAVEL.value,
    "akasa": CategoryEnum.TRAVEL.value,
    "cleartrip": CategoryEnum.TRAVEL.value,
    "yatra": CategoryEnum.TRAVEL.value,
    "fastag": CategoryEnum.TRAVEL.value,
    "zoomcar": CategoryEnum.TRAVEL.value,

    # --- Shopping & E-Commerce ---
    "amazon": CategoryEnum.SHOPPING.value,
    "flipkart": CategoryEnum.SHOPPING.value,
    "myntra": CategoryEnum.SHOPPING.value,
    "ajio": CategoryEnum.SHOPPING.value,
    "nykaa": CategoryEnum.SHOPPING.value,
    "tata cliq": CategoryEnum.SHOPPING.value,
    "meesho": CategoryEnum.SHOPPING.value,
    "croma": CategoryEnum.SHOPPING.value,
    "reliance digital": CategoryEnum.SHOPPING.value,
    "decathlon": CategoryEnum.SHOPPING.value,
    "lenskart": CategoryEnum.SHOPPING.value,
    "zudio": CategoryEnum.SHOPPING.value,
    "westside": CategoryEnum.SHOPPING.value,
    "uniqlo": CategoryEnum.SHOPPING.value,
    "zara": CategoryEnum.SHOPPING.value,
    "h&m": CategoryEnum.SHOPPING.value,
    "ikea": CategoryEnum.SHOPPING.value,

    # --- Subscriptions & Entertainment ---
    "netflix": CategoryEnum.SUBSCRIPTIONS.value,
    "spotify": CategoryEnum.SUBSCRIPTIONS.value,
    "youtube": CategoryEnum.SUBSCRIPTIONS.value,
    "hotstar": CategoryEnum.SUBSCRIPTIONS.value,
    "prime video": CategoryEnum.SUBSCRIPTIONS.value,
    "apple": CategoryEnum.SUBSCRIPTIONS.value,
    "sonyliv": CategoryEnum.SUBSCRIPTIONS.value,
    "zee5": CategoryEnum.SUBSCRIPTIONS.value,
    "gaana": CategoryEnum.SUBSCRIPTIONS.value,
    "jiosaavn": CategoryEnum.SUBSCRIPTIONS.value,
    "chatgpt": CategoryEnum.SUBSCRIPTIONS.value,
    "openai": CategoryEnum.SUBSCRIPTIONS.value,
    "google one": CategoryEnum.SUBSCRIPTIONS.value,
    "bookmyshow": CategoryEnum.SUBSCRIPTIONS.value,

    # --- Investments & Broking ---
    "zerodha": CategoryEnum.INVESTMENTS.value,
    "groww": CategoryEnum.INVESTMENTS.value,
    "kuvera": CategoryEnum.INVESTMENTS.value,
    "upstox": CategoryEnum.INVESTMENTS.value,
    "angel one": CategoryEnum.INVESTMENTS.value,
    "indmoney": CategoryEnum.INVESTMENTS.value,
    "nippon": CategoryEnum.INVESTMENTS.value,
    "cams": CategoryEnum.INVESTMENTS.value,
    "kfintech": CategoryEnum.INVESTMENTS.value,
    "et money": CategoryEnum.INVESTMENTS.value,
    "smallcase": CategoryEnum.INVESTMENTS.value,
    "uti mutual fund": CategoryEnum.INVESTMENTS.value,
    "hdfc mutual fund": CategoryEnum.INVESTMENTS.value,
    "sbi mutual fund": CategoryEnum.INVESTMENTS.value,

    # --- Bills & Utilities ---
    "airtel": CategoryEnum.BILLS.value,
    "jio": CategoryEnum.BILLS.value,
    "vi": CategoryEnum.BILLS.value,
    "vodafone": CategoryEnum.BILLS.value,
    "bsnl": CategoryEnum.BILLS.value,
    "bescom": CategoryEnum.BILLS.value,
    "tata power": CategoryEnum.BILLS.value,
    "adani electricity": CategoryEnum.BILLS.value,
    "tata play": CategoryEnum.BILLS.value,
    "tata sky": CategoryEnum.BILLS.value,
    "dishtv": CategoryEnum.BILLS.value,
    "act fibernet": CategoryEnum.BILLS.value,
    "airtel broadband": CategoryEnum.BILLS.value,
    "igl": CategoryEnum.BILLS.value,
    "mgl": CategoryEnum.BILLS.value,
    "mahanagar gas": CategoryEnum.BILLS.value,

    # --- Rent ---
    "nobroker": CategoryEnum.RENT.value,
    "nestaway": CategoryEnum.RENT.value,
    "mygate rent": CategoryEnum.RENT.value,
    "housing.com": CategoryEnum.RENT.value,

    # --- EMI & Loans & Cards ---
    "bajaj finserv": CategoryEnum.EMI.value,
    "home credit": CategoryEnum.EMI.value,
    "tata capital": CategoryEnum.EMI.value,
    "cred": CategoryEnum.EMI.value,
}


def normalize_text(text: str) -> str:
    """Normalize text for consistent merchant matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def find_merchant(description: str) -> Optional[Tuple[str, str, float]]:
    """
    Search for a recognized merchant in the description.
    Returns:
        tuple of (canonical_merchant_name, category, confidence) or None.
        confidence: 0.85 for exact match, 0.70 for fuzzy match.
    """
    if not description:
        return None

    normalized_desc = normalize_text(description)
    tokens = normalized_desc.split()

    # 1. Check for exact substring / word match (multi-word merchants first, sorted by length desc)
    sorted_merchants = sorted(MERCHANT_CATEGORIES.keys(), key=len, reverse=True)
    for merchant in sorted_merchants:
        # Check boundary match or substring in normalized text
        pattern = r"\b" + re.escape(merchant) + r"\b"
        if re.search(pattern, normalized_desc):
            return merchant.title(), MERCHANT_CATEGORIES[merchant], 0.85

    # 2. Check direct substring match
    for merchant in sorted_merchants:
        if merchant in normalized_desc:
            return merchant.title(), MERCHANT_CATEGORIES[merchant], 0.85

    # 3. Fuzzy match against tokens for typos / minor variations
    for token in tokens:
        if len(token) < 4:
            continue
        for merchant in sorted_merchants:
            # Only compare if merchant is single word of similar length
            if " " in merchant:
                continue
            ratio = difflib.SequenceMatcher(None, token, merchant).ratio()
            if ratio >= 0.82:
                return merchant.title(), MERCHANT_CATEGORIES[merchant], 0.70

    return None
